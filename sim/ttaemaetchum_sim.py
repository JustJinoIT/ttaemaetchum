"""때맞춤 가정 기반 시뮬레이션 (Monte Carlo)
목적: 명시한 가정 아래에서 '임의 일정 계획'이 실업인정 요건을 못 채우는 빈도와,
      전체 일정을 미리 아는 엔진이 이론상 막을 수 있는 상한을 계산한다.
주의: 실제 수급자 효과 검증이 아니다. 모든 파라미터는 가정이며 민감도 분석으로 범위를 본다.
규칙 출처: 서울고용복지+센터 공지(2022.7.1 개편 기준), 고용24 공지. 현행 여부는 제출 전 재확인.
"""
import numpy as np

# (유형, 회차) -> (기간일수, 총 필요 횟수, 구직활동 최소 횟수, 구직활동만 인정 여부)
RULES = {
    "일반수급자 6차":      (28, 2, 1, False),
    "일반수급자 3차":      (28, 1, 0, False),
    "반복수급자 5차":      (28, 2, 2, True),
    "장기수급자 9차(주1회)": (7, 1, 1, True),   # 회차 기준이 자료마다 달라 제안서에서는 모델링 보류, 참고용
    "60세 이상 3차":       (28, 1, 0, False),
}

def engine_feasible(posts, lecs, total, job_min, jobs_only):
    """전체 일정을 아는 엔진: 하루 1활동 제약 하에서 요건 충족이 가능한지."""
    posts = sorted(posts, reverse=True)           # 마감이 늦은 공고부터 쓴다
    jobs_needed = total if jobs_only else job_min
    # 필요한 구직활동 수만큼 서로 다른 날짜에 배치 가능한지 (마감일 이전, 하루 1건)
    for k_jobs in range(jobs_needed, total + 1):
        k_other = total - k_jobs
        if not jobs_only and k_other > len(lecs):
            continue
        top = sorted(posts[:k_jobs])
        if len(top) < k_jobs:
            continue
        if all(int(d) >= i for i, d in enumerate(top)):
            return True
    return False

def baseline_ok(rng, posts, lecs, P, total, job_min, jobs_only, mean_lead, p_act):
    """임의 계획: 인정일 X일 전에야 시작(X~지수분포), 매일 p_act 확률로 하나 수행."""
    start = max(0.0, P - min(P, rng.exponential(mean_lead)))
    used = set()
    jobs = others = 0
    for day in range(int(np.ceil(start)), P):
        if rng.random() > p_act:
            continue
        avail = [i for i, d in enumerate(posts) if d >= day and i not in used]
        if avail:
            used.add(avail[rng.integers(len(avail))]); jobs += 1
        elif (not jobs_only) and any(int(l) == day for l in lecs):
            others += 1
        if jobs + others >= total and jobs >= job_min and (not jobs_only or jobs >= total):
            return True
    return jobs + others >= total and jobs >= job_min and (not jobs_only or jobs >= total)

def run(rule, n, lam_job, lam_lec, mean_lead, p_act, seed=0, p_forget=0.0):
    P, total, job_min, jobs_only = RULES[rule]
    rng = np.random.default_rng(seed)
    b_fail = e_fail = 0
    for _ in range(n):
        posts = rng.uniform(0, P, rng.poisson(lam_job * P / 28))
        lecs = rng.uniform(0, P, rng.poisson(lam_lec * P / 28))
        forgot = rng.random() < p_forget
        ok_b = (not forgot) and baseline_ok(rng, posts, lecs, P, total, job_min, jobs_only, mean_lead, p_act)
        ok_e = engine_feasible(posts, lecs, total, job_min, jobs_only)
        b_fail += (not ok_b); e_fail += (not ok_e)
    return b_fail / n * 100, e_fail / n * 100

if __name__ == "__main__":
    N = 10000
    base = dict(lam_job=6, lam_lec=4, mean_lead=10, p_act=0.6)
    print(f"[기본 가정] 28일당 매칭 공고 {base['lam_job']}건, 취업특강 {base['lam_lec']}회, "
          f"계획 시작 평균 인정일 {base['mean_lead']}일 전, 하루 수행확률 {base['p_act']}, N={N}/유형")
    print(f"{'유형':<16}{'임의 계획 미충족%':>16}{'엔진 구조적 불가%':>18}")
    for r in RULES:
        b, e = run(r, N, **base)
        print(f"{r:<16}{b:>16.1f}{e:>18.1f}")
    print("※ '임의 계획 미충족%'는 계획 시작 시점 같은 행동 가정에 좌우되어 제안서에서 주장하지 않는다.")
    print("\n[민감도] 일반수급자 6차 / 반복수급자 5차: 임의 계획 미충족% (엔진 구조적 불가%)")
    print(f"{'평균 시작(일 전)':<18}" + "".join(f"{'공고 '+str(l)+'건':>22}" for l in (3, 6, 10)))
    for r in ("일반수급자 6차", "반복수급자 5차"):
        print(f"-- {r}")
        for lead in (3, 7, 10, 14):
            row = f"{lead:<18}"
            for lj in (3, 6, 10):
                b, e = run(r, 4000, lam_job=lj, lam_lec=4, mean_lead=lead, p_act=0.6, seed=1)
                row += f"{b:>14.1f} ({e:>4.1f})"
            print(row)
    print("\n[깜빡 신청 가정] 일반수급자 6차, p_forget 0/3/6%")
    for pf in (0.0, 0.03, 0.06):
        b, e = run("일반수급자 6차", 4000, **base, p_forget=pf, seed=2)
        print(f"p_forget={pf:.2f}  임의 계획 {b:.1f}%  (엔진 구조적 불가 {e:.1f}%, 알림으로 깜빡 신청 방지 가정은 별도)")

    # [문서 5-1 표 재현] 취업특강 쿼터 소진(lam_lec=0), 매칭 공고 28일당 6건, N=10,000
    print("\n[문서 5-1 재현] 엔진 구조적 불가% (특강 쿼터 소진 가정)")
    for r, seed in (("일반수급자 6차", 3), ("반복수급자 5차", 3), ("일반수급자 3차", 3), ("60세 이상 3차", 3)):
        _, e = run(r, 10000, lam_job=6, lam_lec=0, mean_lead=10, p_act=0.6, seed=seed)
        print(f"{r:<14}{e:>6.1f}")
    for lj in (3, 10):
        _, e = run("일반수급자 6차", 10000, lam_job=lj, lam_lec=0, mean_lead=10, p_act=0.6, seed=4)
        print(f"일반수급자 6차 / 매칭 공고 {lj}건: {e:.1f}%")
