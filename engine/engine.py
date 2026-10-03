"""때맞춤 핵심 엔진 프로토타입: 규칙(YAML) + 제약 기반 일정 배치 + 위험 경고."""
from dataclasses import dataclass
from datetime import date, timedelta
import yaml, pathlib

RULES = yaml.safe_load((pathlib.Path(__file__).parent / "rules.yaml").read_text(encoding="utf-8"))

@dataclass
class Cand:
    kind: str            # job | lecture | training | exam | work
    day: date            # job: 마감일, lecture/exam: 시행일, training: 개강일, work: 근로일
    label: str = ""
    matches_target: bool = True   # 구직신청서 직종과 일치 (형식적 구직활동 방지)

def band_for(profile):
    t = RULES["types"][profile["type"]]
    for b in t["bands"]:
        if b["from_round"] <= profile["round"] <= b["to_round"]:
            return b
    raise ValueError("해당 회차 규칙 없음")

def _assign_days(items, today, last_day):
    """하루 1활동, 마감 이전 배치(EDF). 불가능하면 None."""
    used, out = set(), []
    for c in sorted(items, key=lambda c: c.day):
        d = today
        while d in used and d <= c.day:
            d += timedelta(days=1)
        if d > c.day or d > last_day:
            return None
        used.add(d); out.append((d, c))
    return out

def plan(profile, today, rec_day, cands, quota_used=0):
    alerts, band = [], band_for(profile)
    if RULES["mode"] == "points":
        return _plan_points(profile, today, rec_day, cands)
    jobs = [c for c in cands if c.kind == "job" and c.matches_target and today <= c.day < rec_day]
    skipped = [c for c in cands if c.kind == "job" and not c.matches_target]
    lecs = [c for c in cands if c.kind == "lecture" and today <= c.day < rec_day]
    need_job = band["total"] if band["jobs_only"] else band["job_min"]
    need_other = band["total"] - need_job
    if skipped:
        alerts.append(("직종 불일치 공고 제외", "구직신청서 직종과 다른 공고는 형식적 구직활동으로 볼 수 있어 일정에서 뺐다."))
    for c in cands:
        if c.kind == "training":
            if c.day >= rec_day - timedelta(days=1):
                alerts.append(("훈련 요건 불가", f"{c.label} 개강일({c.day})이 인정일({rec_day}) 직전·당일이라 이번 회차 요건에 쓸 수 없다."))
        if c.kind == "work":
            alerts.append(("근로 신고", f"{c.day} 근로는 이후 첫 실업인정일({rec_day})에 신고해야 한다."))
    extra_jobs = need_other if (band["jobs_only"] or not lecs or quota_used >= RULES["quotas"]["lecture_total"]) else 0
    all_jobs = sorted(jobs, key=lambda c: c.day, reverse=True)[: need_job + extra_jobs]
    chosen_lecs = [] if extra_jobs else lecs[:need_other]
    sched = _assign_days(all_jobs, today, rec_day - timedelta(days=1))
    ok = sched is not None and len(all_jobs) == need_job + extra_jobs and len(chosen_lecs) == need_other - extra_jobs
    steps = []
    if sched:
        steps += [(d, f"입사지원: {c.label}") for d, c in sched]
    steps += [(c.day, f"취업특강: {c.label}") for c in chosen_lecs]
    steps.sort()
    if not ok:
        short = (need_job + extra_jobs) - len(all_jobs)
        alerts.append(("요건 충족 위험", f"이번 회차 요건을 채울 후보가 부족하다 (구직활동 {max(short,1)}건 이상 추가 필요). 지원 직종 범위를 넓히거나 후보를 더 찾아야 한다."))
    window = f"{rec_day} {RULES['online_window']['start']}~{RULES['online_window']['end']} 온라인 신청"
    if profile["round"] in RULES["must_attend_rounds"]:
        window = f"{rec_day} 고용센터 출석 필요 ({profile['round']}차)"
    return {"ok": ok, "steps": steps, "alerts": alerts, "apply": window,
            "confirm_rule": bool(band.get("confirm")), "rule": band}

def _plan_points(profile, today, rec_day, cands):
    pts = RULES["points"]
    pool = [c for c in cands if c.kind in ("job", "lecture") and today <= c.day < rec_day and c.matches_target]
    pool.sort(key=lambda c: pts["value"][c.kind] / 1.0, reverse=True)
    total, chosen = 0, []
    for c in pool:
        if total >= pts["target"]:
            break
        chosen.append(c); total += pts["value"][c.kind]
    return {"ok": total >= pts["target"], "points": total, "target": pts["target"],
            "steps": sorted((c.day, f"{c.kind}: {c.label}") for c in chosen), "alerts": [],
            "demo_only": pts["demo_only"]}
