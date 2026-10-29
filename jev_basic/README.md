# 문자 분류 모델 실행 방법

`jev.py`는 예제 문자 10통을 모델별로 순차 처리하며 실행 시간, 토큰 사용량, 추정 비용을 비교합니다.

아래 명령은 프로젝트 폴더의 PowerShell에서 실행합니다.

## 웹 화면에서 클릭해서 실행하기

```powershell
.\venv\Scripts\python.exe web_app.py
```

[문자 분류 비교 화면](http://127.0.0.1:8765)을 열고 모델과 케이스를 선택한 뒤 **동시 실행**을 누릅니다.

- 접힌 카드에서는 8개 모델의 진행률을 한눈에 확인합니다. 진행 막대의 로봇은 실제 완료율에 따라 이동하며 실행 중 달리는 모션, 완료 후 깃발을 표시합니다. 동작 줄이기 설정에서는 모션을 끕니다. JEV는 왼쪽 위에 표시됩니다.
- 카드를 클릭하면 전체 모델 진행도 아래에 선택한 모델의 상세가 펼쳐집니다. 다른 모델의 진행도도 계속 표시되며, 같은 카드를 다시 누르면 상세만 접힙니다.
- 상세에는 10개 문자와 결과를 순서대로 모두 표시합니다. 실행 중 해당 케이스의 응답만 갱신하며, 선택하지 않은 케이스도 구분해 표시합니다.
- 상세 탭: **판단·확률**, **종류별 분포**, **시간·비용**. JEV는 API의 사기 확률과 보기별 확률을 표시하고, 다른 모델은 현재 요청한 분류 결과를 표시합니다. 확률을 정확도로 해석하지 않습니다.
- ChatGPT(Luna·Terra·Sol), Claude(Haiku·Sonnet·Opus), Gemini, JEV는 병렬 실행하며 각 모델 안에서는 케이스를 하나씩 순서대로 처리합니다.
- 각 모델이 종료되면 카드에 완료·중지·오류 상태, 해당 모델의 전체 실행 시간(초), 누적 추정 비용(원화·USD)을 표시합니다. 비용을 알 수 없는 요청이 있으면 일부 비용 미확인으로 표시합니다.
- 상단은 처리한 요청 수·전체 진행률·시간·총비용, 각 카드는 유효한 분류를 받은 케이스 수를 표시합니다. 속도 순위는 표시하지 않습니다.
- 위아래 독립 스크롤은 사용하지 않습니다. 10개 상세 결과는 페이지 전체의 단일 스크롤로 확인합니다.
- **실행 설정**에서 JEV·Gemini·ChatGPT·Claude 제품군, 케이스, 환율을 선택합니다. 제품군 선택 시 API 키가 설정된 소속 모델을 모두 실행하며, 개별 모델 선택은 제공하지 않습니다. 키가 없는 제품군은 선택할 수 없습니다.
- **중지**는 진행 중 요청을 마친 뒤 멈춥니다. API 오류가 난 모델은 남은 케이스를 건너뛰며 다른 모델은 계속 실행합니다.
- API 키는 서버에서만 읽습니다. `.env` 변경 후 서버 재시작·새로고침이 필요합니다.
- 결과는 현재 페이지에서만 유지되며 새로고침, 모델·케이스 변경, 새 실행 시 초기화됩니다.

서버 종료는 터미널에서 `Ctrl+C`를 누릅니다. 아래 CLI 명령도 계속 사용할 수 있으며 문자별 분류 결과를 함께 출력합니다.

Jev의 사기 여부는 확률 50%를 기준으로 표시합니다. 위험도는 내부 0~4점 기대값을 1~5점으로 변환하므로 소수점이 표시됩니다.

## 준비

가상환경을 활성화하고 필요한 패키지를 설치합니다.

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

가상환경을 활성화하지 않는 경우 아래 명령의 `python`을 `.\venv\Scripts\python.exe`로 바꾸면 됩니다.

- **Claude**: `.env`의 `ANTHROPIC_API_KEY`를 사용해 Anthropic API로 직접 호출합니다. AWS 키는 사용하지 않습니다. 확장 사고는 끄고 같은 분류 도구 형식으로 응답을 요청합니다.
- **Jev**: `.env`에 설정한 기존 TypeSafe API 키를 사용합니다.
- **ChatGPT 모델**: `.env`의 `OPENAI_API_KEY=` 뒤에 OpenAI API 키를 입력합니다.
- **Gemini**: `.env`의 `GEMINI_API_KEY=` 뒤에 [Google AI Studio에서 발급한 API 키](https://aistudio.google.com/apikey)를 입력합니다.

## Claude 제품군 돌리기

Haiku 4.5, Sonnet 4.6, Opus 4.6을 각각 실행합니다.

```powershell
python jev.py --models haiku sonnet opus
```

하나만 실행할 수도 있습니다.

```powershell
python jev.py --models haiku
python jev.py --models sonnet
python jev.py --models opus
```

## Jev 돌리기

```powershell
python jev.py --models jev
```

## ChatGPT 돌리기

OpenAI API로 GPT-6 Luna, GPT-5.6 Terra, GPT-6.1 Sol을 각각 실행합니다.

```powershell
python jev.py --models luna terra sol
```

하나만 실행할 수도 있습니다.

```powershell
python jev.py --models luna
python jev.py --models terra
python jev.py --models sol
```

## Gemini 돌리기

Gemini API로 Gemini 3.8 Flash를 실행합니다.

```powershell
python jev.py --models gemini
```

기존 모델과 동일한 문자 시나리오 및 JSON 답변 형식을 사용합니다. 추론 설정은 `low`이고, 출력 토큰 수에는 생각 토큰도 포함됩니다.

비용은 [Google 공식 가격표](https://ai.google.dev/gemini-api/docs/pricing)의 유료 Standard 단가(100만 토큰당 입력 $0.75, 출력 $3.75)로 환산합니다. 무료 할당량은 반영하지 않습니다. 이 단가는 2026년 12월 31일까지이며 이후 실행 시 `jev.py`의 단가를 갱신해야 합니다.

## 전체 다 돌리기

Jev → Haiku → Sonnet → Opus → Luna → Terra → Sol → Gemini 순서로 실행합니다. 한 모델이 문자 시나리오 10통을 모두 처리한 뒤 다음 모델로 넘어갑니다.

```powershell
python jev.py
```

## 적은 수의 문자로 먼저 확인하기

`--limit`으로 모델당 처리할 문자 수를 지정합니다. 1~10을 사용할 수 있으며 기본값은 10입니다.

```powershell
# 전체 모델을 문자 한 통씩 실행
python jev.py --limit 1

# Claude 제품군을 문자 한 통씩 실행
python jev.py --models haiku sonnet opus --limit 1

# Jev를 문자 한 통으로 실행
python jev.py --models jev --limit 1

# ChatGPT 제품군을 문자 한 통씩 실행
python jev.py --models luna terra sol --limit 1

# Gemini를 문자 한 통으로 실행
python jev.py --models gemini --limit 1
```

## 출력 내용

- 문자별 진행 상황, 요청 시간, 입력·출력 토큰 수, 누적 추정 비용
- 모델별 처리 건수, 총 실행 시간, 총 추정 비용
- 정상 완료 시 한 통당 평균 시간·비용 및 100만 통 처리 비용 환산
- 마지막에 모든 모델의 비교 요약

비용은 코드에 설정한 일반 입력·출력 단가로 계산한 USD 추정치입니다. 캐시 할인·캐시 쓰기 할증·세금·별도 계약은 반영하지 않아 실제 청구액과 다를 수 있습니다. 100만 통 환산은 측정 표본을 단순 확대해 계산한 값입니다.

한 모델에서 오류가 발생하면 해당 모델의 측정을 중단하고 다음 모델로 넘어갑니다. 실패한 요청의 비용은 합계에 포함되지 않습니다.

## 원화 비용 표시

웹 화면의 총비용은 원화로 표시하고, 상세 시간·비용 탭에는 케이스별 원화와 USD를 함께 표시합니다. 초기 참고 환율은 $1 = 1,344원(2026-10-16 확인 시세 반올림)이며 실시간 갱신되지 않습니다. **실행 설정** 안에서 환율을 변경하면 기존 결과도 즉시 다시 환산됩니다. 0.01원 미만은 별도로 표시합니다. 실제 카드 청구 환율·수수료와는 다를 수 있습니다.

### 회사 브랜드 디자인

UCanLabs 디자인 가이드의 Vivid Orange `#FF7900`, Deep Navy `#0B3158`, Sky Blue `#AAE2FF`, Off White `#F5F5F5`, Dark Gray `#333333`를 적용했습니다. 헤더는 제공된 공식 오렌지 로고 원본을 비율을 유지해 표시합니다. 서체는 기존 시스템 서체를 유지합니다.

- [디자인 가이드](https://drive.google.com/file/d/1dt-DsO4seOL0152k5YaKbmDDJApND4y7/view)
- [공식 로고 폴더](https://drive.google.com/drive/u/0/folders/19xbawGVQL5QEpnxraThMiWvjI804eFIx)
- 사용 로고: `web/assets/ucanlabs-logo.png` (`logo_orange.png` 원본)
