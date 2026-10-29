import argparse
import json
import os
import time
from contextlib import ExitStack
from pathlib import Path

import boto3
from botocore.config import Config
from dotenv import dotenv_values, load_dotenv
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)
# Claude는 프로젝트 .env 값을 우선 사용한다 (기존 셸 환경변수보다 우선).
_anthropic_key = dotenv_values(ENV_PATH).get("ANTHROPIC_API_KEY")
if _anthropic_key is not None:
    os.environ["ANTHROPIC_API_KEY"] = _anthropic_key
del _anthropic_key

# 실제 사기 수법을 본떠 만든 문자 10통
messages = [
    "[Web발신]\n[카카오] 인증번호 [482913]를 입력해주세요. 타인에게 절대 알려주지 마세요.",
    "엄마 나 폰 액정 깨져서 임시폰으로 연락해. 지금 급하게 결제할 게 있는데 문화상품권 좀 사서 핀번호 보내줄 수 있어?",
    "[Web발신]\n[국민건강보험] 홍길동님, 2026년 건강검진 대상자입니다. 기간 내 가까운 검진기관에서 받으세요.",
    "[Web발신]\n[국민건강보험] 건강검진 결과 통보서 발송. 확인하기 → hxxp://nhis-check.top",
    "[Web발신]\n[신한카드] 홍*동님 10/13 14:22 59,000원 일시불 승인 (주)쿠팡",
    "[Web발신]\n[국제발신] 해외결제 980,000원 승인완료. 본인 아닐 시 고객센터 02-XXXX-XXXX 문의",
    "[Web발신]\n교통법규 위반 과태료 고지서가 발송되었습니다. 상세내용 확인 → bit.ly/fine-gov",
    "[Web발신]\n고객님이 주문하신 상품이 출고되었습니다. 운송장번호 6842-1937-5521 (CJ대한통운)",
    "청첩장 보내드립니다. 참석 여부 확인 부탁드려요 ^^ → han.gl/wedding2026",
    "[Web발신]\n(광고) 올리브영 회원님, 10월 올영세일 시작! 최대 70% 할인 무료수신거부 080-022-0000",
]
종류 = {
    "택배 사칭": "택배사나 배송을 사칭한 사기 문자",
    "기관 사칭": "정부, 은행, 공공기관을 사칭한 사기 문자",
    "지인 사칭": "가족이나 지인을 사칭한 사기 문자",
    "그냥 광고": "상품이나 서비스를 홍보하는 광고 문자",
    "정상 안내": "사기도 광고도 아닌 정상적인 안내 문자",
}


# Jev: 앞에서 본 것과 같은 질문 3개
def ask_jev(client, sms):
    response = client.system_one(state=sms, questions={
        "사기_문자인가": Noul(instructions="이 문자는 돈이나 개인정보를 노리는 사기 문자인가?"),
        "어떤_종류인가": Choice(instructions="이 문자는 어떤 종류인가?", criteria=종류),
        "얼마나_위험한가": Score(instructions="이 문자를 받은 사람에게 얼마나 위험한가?", criteria=["1점", "2점", "3점", "4점", "5점"]),
    })
    answers = response.answers
    probability = answers["사기_문자인가"].noul
    return pack_result(response.usage.input_tokens, response.usage.output_tokens, {
        "is_scam": "예" if probability >= 0.5 else "아니오",
        "kind": answers["어떤_종류인가"].choice,
        # Jev의 기준 인덱스는 0부터 시작하므로 표시용 1~5점으로 변환.
        "risk": answers["얼마나_위험한가"].score + 1,
        "scam_probability": probability,
        "kind_probabilities": dict(answers["어떤_종류인가"].probabilities),
    })


# 클로드: 같은 질문 3개를 주고, 정해 둔 형식으로만 답하게 함
답_형식 = {"toolSpec": {"name": "answer", "inputSchema": {"json": {
    "type": "object",
    "properties": {
        "is_scam": {"type": "string", "enum": ["예", "아니오"], "description": "사기 문자인가?"},
        "kind": {"type": "string", "enum": list(종류), "description": "어떤 종류인가?"},
        "risk": {"type": "integer", "minimum": 1, "maximum": 5, "description": "얼마나 위험한가? (1~5점)"},
    },
    "required": ["is_scam", "kind", "risk"],
    "additionalProperties": False,
}}}}


def ask_claude(bedrock, model, sms):
    response = bedrock.converse(
        modelId=model,
        messages=[{"role": "user", "content": [{"text": "이 문자를 보고 판단해 주세요.\n\n" + sms}]}],
        toolConfig={"tools": [답_형식], "toolChoice": {"tool": {"name": "answer"}}},
    )
    answer = next((part["toolUse"]["input"] for part in response["output"]["message"]["content"]
                   if part.get("toolUse", {}).get("name") == "answer"), None)
    return pack_result(response["usage"]["inputTokens"], response["usage"]["outputTokens"], answer)


def ask_anthropic(client, model, sms):
    response = client.messages.create(
        model=model,
        max_tokens=512,
        messages=[{"role": "user", "content": "이 문자를 보고 판단해 주세요.\n\n" + sms}],
        tools=[{"name": "answer", "description": "문자의 사기 여부, 종류, 위험도를 분류합니다.",
                "input_schema": 답_형식["toolSpec"]["inputSchema"]["json"]}],
        tool_choice={"type": "tool", "name": "answer"},
        thinking={"type": "disabled"},
    )
    answer = next((part.input for part in response.content
                   if part.type == "tool_use" and part.name == "answer"), None)
    return pack_result(response.usage.input_tokens, response.usage.output_tokens, answer)


def ask_openai(client, model, sms):
    response = client.responses.create(
        model=model,
        input="이 문자를 보고 판단해 주세요.\n\n" + sms,
        reasoning={"effort": "low"},
        text={"format": {
            "type": "json_schema", "name": "answer", "strict": True,
            "schema": 답_형식["toolSpec"]["inputSchema"]["json"],
        }},
        store=False,
    )
    return pack_result(response.usage.input_tokens, response.usage.output_tokens, response.output_text)


def ask_gemini(client, model, sms):
    response = client.models.generate_content(
        model=model,
        contents="이 문자를 보고 판단해 주세요.\n\n" + sms,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": 답_형식["toolSpec"]["inputSchema"]["json"],
            "thinking_config": {"thinking_level": "LOW"},
        },
    )
    usage = response.usage_metadata
    if usage is None or usage.prompt_token_count is None or usage.candidates_token_count is None:
        raise ValueError("Gemini가 토큰 사용량을 반환하지 않았습니다")
    # candidates_token_count에는 생각 토큰이 포함되지 않으며 둘 다 출력 단가로 과금됨.
    return pack_result(usage.prompt_token_count,
                       usage.candidates_token_count + (usage.thoughts_token_count or 0), response.text)


def pack_result(input_tokens, output_tokens, answer):
    """응답이 거절되거나 형식이 틀려도 보고된 토큰 비용은 보존한다."""
    result = {"input_tokens": input_tokens, "output_tokens": output_tokens, "answer": None}
    try:
        if isinstance(answer, str):
            answer = json.loads(answer)
        if not isinstance(answer, dict) or answer.get("is_scam") not in ("예", "아니오"):
            raise ValueError()
        risk = answer.get("risk")
        if (answer.get("kind") not in 종류 or isinstance(risk, bool)
                or not isinstance(risk, (int, float)) or not 1 <= risk <= 5):
            raise ValueError()
        result["answer"] = answer
    except (ValueError, TypeError):
        result["answer_error"] = "분류 응답이 없거나 형식이 올바르지 않습니다 (거절/출력 제한 등)."
    return result


# 이름, 제공자, API 모델 ID, 100만 토큰당 USD (입력, 출력).
# 2026-10-15 확인. Jev는 기존 단가 유지.
# https://developers.openai.com/api/docs/pricing
# https://developers.openai.com/api/docs/models/gpt-5.6-terra
# https://ai.google.dev/gemini-api/docs/pricing (Gemini: 2026-12-31까지 유료 Standard 단가)
모델들 = {
    "jev": ("Jev", "jev", "jev-latest", (0.042, 0)),
    "haiku": ("Claude Haiku 4.5", "anthropic", "claude-haiku-4-5-20251001", (1, 5)),
    "sonnet": ("Claude Sonnet 4.6", "anthropic", "claude-sonnet-4-6", (3, 15)),
    "opus": ("Claude Opus 4.6", "anthropic", "claude-opus-4-6", (5, 25)),
    "luna": ("GPT-6 Luna", "openai", "gpt-6-luna", (0.1, 0.5)),
    "terra": ("GPT-5.6 Terra", "openai", "gpt-5.6-terra", (2, 12)),
    "sol": ("GPT-6.1 Sol", "openai", "gpt-6.1-sol", (2, 10)),
    "gemini": ("Gemini 3.8 Flash", "gemini", "gemini-3.8-flash", (0.75, 3.75)),
}


def 측정(이름, ask, 단가, 문자들):
    입력 = 출력 = 완료 = 0
    start = time.perf_counter()
    print(f"\n[{이름}] {len(문자들)}통 시작", flush=True)
    오류 = None
    for 번호, sms in enumerate(문자들, 1):
        print(f"  [{번호}/{len(문자들)}] 요청 중...", end=" ", flush=True)
        요청_시작 = time.perf_counter()
        try:
            result = ask(sms)
            i, o = result["input_tokens"], result["output_tokens"]
            if i is None or o is None:
                raise ValueError("API가 토큰 사용량을 반환하지 않았습니다")
        except Exception as exc:
            오류 = f"{type(exc).__name__}: {exc}"
            print(f"실패 ({time.perf_counter() - 요청_시작:.2f}초)\n  {오류}", flush=True)
            break  # 인증/권한 오류 등에서 같은 요청을 반복하지 않음
        입력, 출력, 완료 = 입력 + i, 출력 + o, 완료 + 1
        비용 = (입력 * 단가[0] + 출력 * 단가[1]) / 1_000_000
        print(f"{time.perf_counter() - 요청_시작:.2f}초 | 토큰 {i:,}/{o:,} (입력/출력)"
              f" | 누적 추정 ${비용:.6f}", flush=True)
        print(f"    문자: {sms}", flush=True)
        answer = result["answer"]
        print(f"    분류: 사기 {answer['is_scam']} | {answer['kind']} | 위험도 {answer['risk']:.2f}/5"
              if answer else f"    {result['answer_error']}", flush=True)
    걸린_시간 = time.perf_counter() - start
    비용 = (입력 * 단가[0] + 출력 * 단가[1]) / 1_000_000
    요약 = f"{이름} | {완료}/{len(문자들)}통 | 총 {걸린_시간:.2f}초 | 추정 ${비용:.6f}"
    if 완료:
        요약 += f" | 토큰 {입력:,}/{출력:,}"
        if not 오류:
            요약 += (f" | 한 통 {걸린_시간 / 완료:.2f}초 / ${비용 / 완료:.6f}"
                     f" | 100만 통 환산 ${비용 / 완료 * 1_000_000:,.2f}")
    if 오류:
        요약 += " | 중단: 실패 요청 비용 미포함"
    print(요약, flush=True)
    return 요약


def make_ask(key, stack, clients):
    이름, 제공자, model, 단가 = 모델들[key]
    if 제공자 not in clients:
        if 제공자 == "jev":
            clients[제공자] = stack.enter_context(TypeSafeClient(model=model))
        elif 제공자 == "anthropic":
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise RuntimeError(".env에 ANTHROPIC_API_KEY를 설정해 주세요")
            from anthropic import Anthropic
            clients[제공자] = stack.enter_context(Anthropic(
                api_key=os.environ["ANTHROPIC_API_KEY"], timeout=120, max_retries=0))
        elif 제공자 == "bedrock":
            clients[제공자] = boto3.client(
                "bedrock-runtime", region_name=os.getenv("AWS_REGION", "ap-northeast-2"),
                config=Config(connect_timeout=10, read_timeout=120,
                              retries={"total_max_attempts": 1}),
            )
            stack.callback(clients[제공자].close)
        elif 제공자 == "gemini":
            if not os.getenv("GEMINI_API_KEY"):
                raise RuntimeError(".env에 GEMINI_API_KEY를 설정해 주세요")
            from google import genai
            clients[제공자] = genai.Client(
                api_key=os.environ["GEMINI_API_KEY"],
                http_options={"timeout": 120_000, "retry_options": {"attempts": 1}},
            )
            stack.callback(clients[제공자].close)
        else:
            if not os.getenv("OPENAI_API_KEY"):
                raise RuntimeError(".env에 OPENAI_API_KEY를 설정해 주세요")
            from openai import OpenAI
            clients[제공자] = stack.enter_context(OpenAI(timeout=120, max_retries=0))
    client = clients[제공자]
    if 제공자 == "jev":
        ask = lambda sms: ask_jev(client, sms)
    elif 제공자 == "anthropic":
        ask = lambda sms: ask_anthropic(client, model, sms)
    elif 제공자 == "bedrock":
        ask = lambda sms: ask_claude(client, model, sms)
    elif 제공자 == "gemini":
        ask = lambda sms: ask_gemini(client, model, sms)
    else:
        ask = lambda sms: ask_openai(client, model, sms)
    return ask


def main():
    parser = argparse.ArgumentParser(description="문자 분류 모델별 시간·토큰·추정 비용 비교")
    parser.add_argument("--models", nargs="+", choices=모델들, default=list(모델들))
    parser.add_argument("--limit", type=int, default=len(messages), help="모델별 문자 수 (1~10)")
    args = parser.parse_args()
    if not 1 <= args.limit <= len(messages):
        parser.error(f"--limit은 1~{len(messages)}이어야 합니다")
    print("비용은 응답 토큰 × 일반 입력/출력 단가의 USD 추정치입니다.\n"
          "캐시 할인·캐시 쓰기 할증·세금·별도 계약은 미반영이며 실제 청구액과 다를 수 있습니다.\n"
          "시간은 순차 API 요청의 대기 시간을 포함합니다. OpenAI/Gemini 추론 설정=low.\n"
          "Gemini는 무료 할당량 적용 전 유료 Standard 단가로 환산합니다 (2026-12-31까지 단가).", flush=True)
    요약들 = []
    with ExitStack() as stack:
        clients = {}
        for key in dict.fromkeys(args.models):
            이름, 제공자, model, 단가 = 모델들[key]
            try:
                ask = make_ask(key, stack, clients)
                요약들.append(측정(이름, ask, 단가, messages[:args.limit]))
            except Exception as exc:
                요약들.append(f"{이름} | 실행 불가: {type(exc).__name__}: {exc}")
                print(요약들[-1], flush=True)
    print("\n=== 모델별 최종 비교 ===", flush=True)
    print("\n".join(요약들), flush=True)


if __name__ == "__main__":
    main()
