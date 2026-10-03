# 때맞춤 (ttaemaetchum)

실업인정 일정 엔진 프로토타입입니다. 수급자가 고용센터 실업인정 신청(주기는 1~4주) 전까지 구직활동, 구직외활동(취업특강·직업훈련·자격시험 등), 근로 일정을 규칙에 맞게 배치하고, 규칙 위반 위험이 있으면 경고합니다.

- 규칙은 `rules.yaml`에 분리되어 있어 코드 수정 없이 값을 바꿀 수 있습니다.
- 일정 배치는 마감일 우선(EDF) 방식으로 하루 1개 활동을 배정합니다.
- 일반·반복·60세 이상 수급자 유형별 회차 규칙을 지원합니다.

> **이 저장소는 설계 검증용 프로토타입이다. 시뮬레이션은 실제 수급자 검증이 아니며 모든 파라미터는 가정값이다. rules.yaml 의 confirm: true 값과 점수형 값은 공식 기준이 아니다. 최종 인정 여부는 관할 고용센터에서 확인해야 한다.**

## 폴더 구성

| 경로 | 내용 |
|---|---|
| `engine/` | 핵심 엔진. `engine.py`(배치·경고 로직), `rules.yaml`(규칙 설정), `scenarios.py`(시나리오 예시), `test_engine.py`(테스트 8개) |
| `sim/` | 시뮬레이션 스크립트 `ttaemaetchum_sim.py` (Monte Carlo, 가정 기반) |
| `submission/` | 공모전 제출물(제안서 PDF 및 미리보기) |

## 실행 방법

요구 사항: Python 3.10 이상

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install pyyaml numpy pytest

cd engine
python test_engine.py              # "8개 테스트 통과" 출력 확인
```

시뮬레이션은 `sim/` 안에서 실행합니다. 출력 중 "임의 계획 미충족%"는 계획 시작 시점 등 행동 가정에 좌우되므로 효과 근거로 쓰지 않는다.

```bash
cd sim
python ttaemaetchum_sim.py
```
