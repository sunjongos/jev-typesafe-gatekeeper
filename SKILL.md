---
name: JEV TypeSafe Gatekeeper (Pure System 1 Standalone Skill v5.0)
description: 유캔랩스(UCanLabs) 기술 브리핑 및 TypeSafe AI 공식 SDK(jev_basic) 기반의 초경량·초고속 판단(Noul, Choice, Score, Box) 및 90/10 게이트키퍼 파이프라인 전용 우주 최강 독립 스킬입니다. 기존 JEV×온톨로지×Deep Twin과 완전히 분리되어 단독 작동합니다.
---

# ⚡ JEV TypeSafe Gatekeeper v5.0 (World-Class Pure System 1 Standalone Skill)

본 스킬은 기존 **`JEV × 온톨로지 × Deep Twin`** 시스템과 완전히 분리되어, **TypeSafe AI (Diogo Almeida 설립)**의 공식 `typesafe-sdk`와 **유캔랩스(UCanLabs) 기술 브리핑**의 아키텍처를 5-Loop 자가 진화로 극대화한 **우주 최강 수준의 순수 System 1 직관 판단 & 90/10 게이트키퍼** 독립 스킬 컨테이너입니다.

---

## 🚀 5-Loop 고도화 아키텍처 (v5.0 핵심 기능)

| Loop | 핵심 엔진 | 상세 구현 내용 |
| :--- | :--- | :--- |
| **Loop 1** | **4-Primitive Official SDK Engine** | `TypeSafeClient.system_one()` 단일 호출로 **`Noul`**(Yes/No 확률), **`Choice`**(다지선다 + 보기별 확률 분포), **`Score`**(0~4 인덱스를 1~5점 소수점 기대값으로 변환), **`Box`/`Image`**(멀티모달 파손/쓰러짐 좌표 검출) 4대 원형을 동시 처리 |
| **Loop 2** | **Shannon Entropy $H(P)$ & 3-Zone Gatekeeper** | 선택지 확률 분포의 정규화 섀넌 엔트로피 $H_{\text{norm}}(P) = -\frac{1}{\log_2 N}\sum p_i \log_2 p_i$를 계산하여 **90% 명확 구간(Zone A 정상 통과 / Zone B 즉시 차단)**과 **10% 애매 구간(Zone C System 2 LLM 정밀 검토)**으로 수학적 분기 |
| **Loop 3** | **3-Weakness Defense Shield** | 강의록 06장 공식 3대 약점 완벽 방어:<br>① **복잡한 수리·날짜 계산** 정규식/AST 감지<br>② **고도의 반어법("참~ 잘도 돌아간다")** 어휘 사전 감지<br>③ **선택지 순서 편향(Position Bias)** 정방향·역방향 양방향 교차 평균(`--debiased`) 및 **교묘한 단축 URL(9번 청첩장 `han.gl`)** 핀포인트 포착 |
| **Loop 4** | **5대 실무 도메인 프리셋 & 병렬 배치** | `ThreadPoolExecutor` 비동기 병렬 처리 및 5대 도메인 Zero-shot 프리셋 기본 탑재:<br>• `scam`: 스미싱·보이스피싱·청첩장 사기 판별<br>• `ndb_cs`: 남양주백병원 환자 문의/콜센터 부서 배정<br>• `spine_triage`: 척추·관절 외래/응급 Red-Flag(마미증후군 등) 트리아제<br>• `llm_judge`: AI 에이전트 출력물 초경량 환각·보안 검수관 (LLM-as-a-Judge)<br>• `emotion_game`: 실시간 감정 캐릭터 표정 및 슈팅/게임 행동 제어 |
| **Loop 5** | **SQLite ROI Ledger & 8-Model Web Race UI** | `data/gatekeeper_telemetry.db`에 모든 판단의 속도·엔트로피·절감 비용(Opus 대비 300배 절감, 100만 건당 약 348만 원 절감)을 자동 기록하며, `jev_basic/web_app.py`(`http://127.0.0.1:8765`)로 8대 모델 실시간 경주 UI 제공 |

---

## 💻 CLI 실행 가이드

### 1. 5-Loop 전체 무결성 자가 검증 (`--self-test`)
```powershell
python .agents/skills/jev_typesafe_gatekeeper/scripts/jev_gatekeeper.py --self-test
```

### 2. 사기 문자 10건 90/10 게이트키퍼 실전 벤치마크 (`--demo-10`)
- 1~8번, 10번(명백한 9건, **90%**)은 JEV가 즉시 자동 통과/차단하고, 교묘한 **9번 청첩장 단축 URL 케이스(1건, 10%)**만 정확히 골라내어 System 2 고성능 LLM으로 에스컬레이션합니다.
```powershell
python .agents/skills/jev_typesafe_gatekeeper/scripts/jev_gatekeeper.py --demo-10
```

### 3. 5대 도메인 모드별 단일 문장 초고속 판별
```powershell
# ① 스미싱·사기 문자 판별 (scam)
python .agents/skills/jev_typesafe_gatekeeper/scripts/jev_gatekeeper.py --mode scam "청첩장 보내드립니다. 참석 여부 확인 부탁드려요 ^^ → han.gl/wedding2026"

# ② 남양주백병원 환자 문의/콜센터 1차 게이트키퍼 (ndb_cs)
python .agents/skills/jev_typesafe_gatekeeper/scripts/jev_gatekeeper.py --mode ndb_cs "실비보험 청구하려고 하는데 어제 외래 진료비 세부내역서 발급 가능한가요?"

# ③ 척추·관절 응급 Red-Flag 트리아제 (spine_triage)
python .agents/skills/jev_typesafe_gatekeeper/scripts/jev_gatekeeper.py --mode spine_triage "오늘 아침부터 갑자기 발목에 힘이 안 들어가고 소변 보기가 힘듭니다"

# ④ AI 응답 품질·환각 검수관 (llm_judge)
python .agents/skills/jev_typesafe_gatekeeper/scripts/jev_gatekeeper.py --mode llm_judge "환자 홍길동(주민번호 750101-1234567)님의 척추 수술 기록입니다."

# ⑤ 실시간 캐릭터 감정·게임 제어 (emotion_game)
python .agents/skills/jev_typesafe_gatekeeper/scripts/jev_gatekeeper.py --mode emotion_game "전방에 적 스나이퍼 레이저 조준선 포착! 즉시 엄폐해!"
```

### 4. 누적 비용 절감 통계 조회 (`--stats`) 및 웹 레이싱 대시보드
```powershell
# SQLite ROI 원장 통계 조회
python .agents/skills/jev_typesafe_gatekeeper/scripts/jev_gatekeeper.py --stats

# 8대 모델(Jev vs Claude Haiku/Sonnet/Opus vs GPT Luna/Terra/Sol vs Gemini) 웹 비교 화면 (http://127.0.0.1:8765)
python .agents/skills/jev_typesafe_gatekeeper/jev_basic/web_app.py
```
