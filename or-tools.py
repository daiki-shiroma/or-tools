from ortools.sat.python import cp_model

def get_assignment_data():
    return {
        "workers": ['Aさん', 'Bさん', 'Cさん', 'Dさん'],
        "tasks": ['PJ-1 (重要度高)', 'PJ-2 (納期近)', 'PJ-3 (専門性要)'],
        "costs": {
            ('Aさん', 'PJ-1 (重要度高)'): 100, ('Aさん', 'PJ-2 (納期近)'): 150, ('Aさん', 'PJ-3 (専門性要)'): 250,
            ('Bさん', 'PJ-1 (重要度高)'): 120, ('Bさん', 'PJ-2 (納期近)'): 90,  ('Bさん', 'PJ-3 (専門性要)'): 180,
            ('Cさん', 'PJ-1 (重要度高)'): 150, ('Cさん', 'PJ-2 (納期近)'): 100, ('Cさん', 'PJ-3 (専門性要)'): 110,
            ('Dさん', 'PJ-1 (重要度高)'): 130, ('Dさん', 'PJ-2 (納期近)'): 110, ('Dさん', 'PJ-3 (専門性要)'): 95
        },
        "required_skills": {
            'PJ-1 (重要度高)':
              {'プログラミング': 2, 'デザイン': 0},
            'PJ-2 (納期近)': {'プログラミング': 0, 'デザイン': 1},
            'PJ-3 (専門性要)': {'プログラミング': 1, 'デザイン': 2}
        },
        "worker_skills": {
            'Aさん': {'プログラミング': 2, 'デザイン': 1},
            'Bさん': {'プログラミング': 1, 'デザイン': 0},
            'Cさん': {'プログラミング': 0, 'デザイン': 2},
            'Dさん': {'プログラミング': 3, 'デザイン': 1}
        },
        "project_budgets": {
            'PJ-1 (重要度高)': 130,
            'PJ-2 (納期近)': 100,
            'PJ-3 (専門性要)': 120
        },
        "worker_preferences": {
            ('Aさん', 'PJ-1 (重要度高)'): 2, ('Aさん', 'PJ-2 (納期近)'): 1, ('Aさん', 'PJ-3 (専門性要)'): 0,
            ('Bさん', 'PJ-1 (重要度高)'): 1, ('Bさん', 'PJ-2 (納期近)'): 2, ('Bさん', 'PJ-3 (専門性要)'): 1,
            ('Cさん', 'PJ-1 (重要度高)'): 0, ('Cさん', 'PJ-2 (納期近)'): 1, ('Cさん', 'PJ-3 (専門性要)'): 2,
            ('Dさん', 'PJ-1 (重要度高)'): 1, ('Dさん', 'PJ-2 (納期近)'): 1, ('Dさん', 'PJ-3 (専門性要)'): 2
        }
    }


def solve_personnel_assignment(data):
    model = cp_model.CpModel()

    workers = data["workers"]
    tasks = data["tasks"]
    costs = data["costs"]
    required_skills = data["required_skills"]
    worker_skills = data["worker_skills"]
    project_budgets = data["project_budgets"]
    worker_preferences = data["worker_preferences"]

    # modelの定義
    model = cp_model.CpModel()

    # --- 変数定義 ---
    # x_ij は社員iがタスクjに割り当てられる場合に1、そうでなければ0
    x = {}
    for w in workers:
        for t in tasks:
            x[(w, t)] = model.NewBoolVar(f'x_{w}_{t}')

    # --- 目的関数: 総コストの最小化 ---
    # total_cost_expr = sum(costs[(w, t)] * x[(w, t)] for w in workers for t in tasks)
    # model.Minimize(total_cost_expr)
    # 目的関数に希望度ペナルティを入れる
    PENALTY = 1000
    total_cost_expr = sum(
      costs[(w, t)] * x[(w, t)] +
      (PENALTY if worker_preferences[(w, t)] == 0 else 0) * x[(w, t)]
      for w in workers for t in tasks
    )
    model.Minimize(total_cost_expr)

    # --- 5. 制約条件 (多様な制約の例) ---

    # 5-1. 各タスクにはちょうど1人割り当てる
    for t in tasks:
        model.Add(sum(x[(w, t)] for w in workers) == 1)

    # 5-2. 各社員は最大で1つのタスクに割り当てる (兼務しない場合)
    for w in workers:
        model.Add(sum(x[(w, t)] for t in tasks) <= 1)

    # 5-3. スキル制約: タスクの必須スキルを満たす社員のみ割り当て可能
    for w in workers:
        for t in tasks:
            for skill_name, required_level in required_skills[t].items():
                if required_level >= 2: # スキルが必要な場合
                    # 社員のスキルがタスクの要求スキルを満たさない場合、割り当てられないようにする
                    if worker_skills[w][skill_name] < required_level:
                        model.Add(x[(w, t)] == 0)

    # 5-4. プロジェクト予算制約: 各プロジェクトの割り当てコストが予算を超過しない
    for t in tasks:
        # 割り当てられた社員のコスト合計が予算以下
        model.Add(sum(costs[(w, t)] * x[(w, t)] for w in workers) <= project_budgets[t])

    # 5-5. 社員の希望制約: 希望度が低いタスクには割り当てない (希望度0のタスクは強制的に割り当てなし)
    for w in workers:
        for t in tasks:
            if worker_preferences[(w, t)] == 0:
                model.Add(x[(w, t)] == 0)

    # --- 6. 問題を解く ---
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # --- 7. 結果の表示 ---
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"Status: {solver.StatusName(status)}")
        print(f"Total Cost = {solver.ObjectiveValue()}")
        print("\n--- 割り当て結果 ---")
        for w in workers:
            for t in tasks:
                if solver.BooleanValue(x[(w, t)]):
                    print(f"社員 {w} が {t} に割り当てられました。 (コスト: {costs[(w, t)]})")
    else:
        print("最適な解が見つかりませんでした。")


if __name__ == "__main__":
 data = get_assignment_data()
 solve_personnel_assignment(data)