import engine, scenarios as S
from engine import plan
from datetime import date as D

def test_A_training_not_countable_two_jobs():
    r = plan(**S.A)
    assert r["ok"] and len(r["steps"]) == 2 and all("입사지원" in s for _, s in r["steps"])
    titles = [t for t, _ in r["alerts"]]
    assert "훈련 요건 불가" in titles and "근로 신고" in titles
    assert r["apply"].endswith("온라인 신청") and "00:00~17:00" in r["apply"]

def test_B_repeat_jobs_only_needs_two_jobs():
    assert plan(**S.B_ok)["ok"]
    r = plan(**S.B_short)
    assert not r["ok"] and any(t == "요건 충족 위험" for t, _ in r["alerts"])  # 특강으로 대체 불가

def test_C_senior_lecture_ok():
    r = plan(**S.C)
    assert r["ok"] and "취업특강" in r["steps"][0][1]

def test_D_work_report_first_recognition_day():
    r = plan(**S.D_work)
    assert any(t == "근로 신고" and "2026-11-24" in m for t, m in r["alerts"])

def test_mismatched_posting_excluded():
    r = plan(**S.MISMATCH)
    assert any(t == "직종 불일치 공고 제외" for t, _ in r["alerts"])
    assert all("무관" not in s for _, s in r["steps"])

def test_attend_round_4():
    r = plan(profile={"type":"general","round":4}, today=S.TODAY, rec_day=S.REC, cands=[engine.Cand("job", D(2026,11,12), "공고")])
    assert "출석" in r["apply"]

def test_points_mode_demo_flag():
    engine.RULES["mode"] = "points"
    try:
        r = plan(**S.B_ok)          # 입사지원 2건(4+4) + 취업특강(2) = 10점, 시연용 목표 10점
        assert r["demo_only"] and r["ok"] and r["points"] == 10
        assert not plan(**S.A)["ok"]  # 입사지원 2건(8점)만으로는 목표 미달
    finally:
        engine.RULES["mode"] = "count"

def test_deadline_infeasible_when_too_late():
    r = plan(profile={"type":"general","round":6}, today=D(2026,11,20), rec_day=S.REC,
             cands=[engine.Cand("job", D(2026,11,12), "지난 공고"), engine.Cand("job", D(2026,11,21), "남은 공고")])
    assert not r["ok"]

if __name__ == "__main__":
    fns = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for f in fns: f()
    print(f"{len(fns)}개 테스트 통과")
