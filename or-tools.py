# Google OR-Tools を使用して社員をプロジェクトに最適に割り当てる問題を解決するスクリプト
from ortools.sat.python import cp_model

# 割り当てデータを定義する関数
# 各社員、タスク、コスト、スキル、予算、希望度を含むデータを返します
def get_assignment_data():
    return {
        "workers": ['Aさん', 'Bさん', 'Cさん', 'Dさん'],  # 社員リスト
        "tasks": ['PJ-1 (重要度高)', 'PJ-2 (納期近)', 'PJ-3 (専門性要)'],  # タスクリスト
        "costs": {  # 社員とタスクの割り当てコスト
            ('Aさん', 'PJ-1 (重要度高)'): 100, ('Aさん', 'PJ-2 (納期近)'): 150, ('Aさん', 'PJ-3 (専門性要)'): 250,
            ('Bさん', 'PJ-1 (重要度高)'): 120, ('Bさん', 'PJ-2 (納期近)'): 90,  ('Bさん', 'PJ-3 (専門性要)'): 180,
            ('Cさん', 'PJ-1 (重要度高)'): 150, ('Cさん', 'PJ-2 (納期近)'): 100, ('Cさん', 'PJ-3 (専門性要)'): 110,
            ('Dさん', 'PJ-1 (重要度高)'): 130, ('Dさん', 'PJ-2 (納期近)'): 110, ('Dさん', 'PJ-3 (専門性要)'): 95
        },
        "required_skills": {  # 各タスクに必要なスキル
            'PJ-1 (重要度高)': {'プログラミング': 2, 'デザイン': 0},
            'PJ-2 (納期近)': {'プログラミング': 0, 'デザイン': 1},
            'PJ-3 (専門性要)': {'プログラミング': 1, 'デザイン': 2}
        },
        "worker_skills": {  # 社員が持つスキル
            'Aさん': {'プログラミング': 2, 'デザイン': 1},
            'Bさん': {'プログラミング': 1, 'デザイン': 0},
            'Cさん': {'プログラミング': 0, 'デザイン': 2},
            'Dさん': {'プログラミング': 3, 'デザイン': 1}
        },
        "project_budgets": {  # 各プロジェクトの予算
            'PJ-1 (重要度高)': 130,
            'PJ-2 (納期近)': 100,
            'PJ-3 (専門性要)': 120
        },
        "worker_preferences": {  # 社員の希望度(5段階評価)
            ('Aさん', 'PJ-1 (重要度高)'): 5, ('Aさん', 'PJ-2 (納期近)'): 3, ('Aさん', 'PJ-3 (専門性要)'): 1,
            ('Bさん', 'PJ-1 (重要度高)'): 3, ('Bさん', 'PJ-2 (納期近)'): 5, ('Bさん', 'PJ-3 (専門性要)'): 4,
            ('Cさん', 'PJ-1 (重要度高)'): 1, ('Cさん', 'PJ-2 (納期近)'): 3, ('Cさん', 'PJ-3 (専門性要)'): 5,
            ('Dさん', 'PJ-1 (重要度高)'): 4, ('Dさん', 'PJ-2 (納期近)'): 3, ('Dさん', 'PJ-3 (専門性要)'): 5
        },
        "worker_overtime": {  # 社員ごとの残業可否
            'Aさん': True,
            'Bさん': False,
            'Cさん': True,
            'Dさん': False
        },
        "worker_hours": {  # 社員ごとの勤務可能時間
            'Aさん': 8,
            'Bさん': 6, # 時短勤務
            'Cさん': 8,
            'Dさん': 4,
        }
    }

# 社員割り当て問題を解く関数
def solve_personnel_assignment(data):
    model = cp_model.CpModel()  # OR-Tools のモデルを初期化

    # データの取得
    workers = data["workers"]
    tasks = data["tasks"]
    costs = data["costs"]
    required_skills = data["required_skills"]
    worker_skills = data["worker_skills"]
    project_budgets = data["project_budgets"]
    worker_preferences = data["worker_preferences"]
    worker_overtime = data["worker_overtime"]
    worker_hours = data["worker_hours"]

    # --- 変数定義 ---
    # x_ij は社員iがタスクjに割り当てられる場合に1、そうでなければ0
    x = {}
    for w in workers:
        for t in tasks:
            x[(w, t)] = model.NewBoolVar(f'x_{w}_{t}')

    # 残業可否変数: overtime_w は社員wが残業可能かどうかを示す二値変数
    overtime = {}
    for w in workers:
        overtime[w] = model.NewBoolVar(f'overtime_{w}')

    # 勤務時間制約変数: hours_w_t は社員wがタスクtに割り当てられる場合の勤務時間
    hours = {}
    for w in workers:
        for t in tasks:
            hours[(w, t)] = model.NewIntVar(0, 8, f'hours_{w}_{t}')  # 最大8時間勤務

    # --- 目的関数: 総コストの最小化 ---
    total_cost_expr = sum(
      costs[(w, t)] * x[(w, t)]
      for w in workers for t in tasks
    )
    model.Minimize(total_cost_expr)

    # --- 制約条件 ---

    # 各タスクには複数人が割り当て可能
    for t in tasks:
        model.Add(sum(x[(w, t)] for w in workers) >= 1)  # 少なくとも1人が割り当てられる

    # スキル合計が要求レベルを満たす制約
    for t in tasks:
        for skill_name, required_level in required_skills[t].items():
            model.Add(
                sum(worker_skills[w][skill_name] * x[(w, t)] for w in workers) >= required_level
            )

    # 勤務時間制約: 各社員の勤務時間がその社員の勤務可能時間を超えない
    for w in workers:
        model.Add(sum(hours[(w, t)] for t in tasks) <= worker_hours[w])

    # 残業可否制約: 残業可能な場合は勤務時間が10時間まで許容される
    for w in workers:
        if worker_overtime[w]:
            model.Add(sum(hours[(w, t)] for t in tasks) <= 10)
        else:
            model.Add(sum(hours[(w, t)] for t in tasks) <= worker_hours[w])

    # 各社員は最大で1つのタスクに割り当てる
    for w in workers:
        model.Add(sum(x[(w, t)] for t in tasks) <= 1)

    # スキル制約: 必須スキルを満たす社員のみ割り当て可能
    for w in workers:
        for t in tasks:
            for skill_name, required_level in required_skills[t].items():
                if required_level >= 2:  # スキルが必要な場合
                    if worker_skills[w][skill_name] < required_level:
                        model.Add(x[(w, t)] == 0)

    # プロジェクト予算制約: 割り当てコストが予算を超過しない
    for t in tasks:
        model.Add(sum(costs[(w, t)] * x[(w, t)] for w in workers) <= project_budgets[t])

    # 希望度制約: 希望度が0のタスクには割り当てない
    for w in workers:
        for t in tasks:
            if worker_preferences[(w, t)] == 0:
                model.Add(x[(w, t)] == 0)

    # --- 問題を解く ---
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # --- 結果の表示 ---
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

# メイン処理
if __name__ == "__main__":
    data = get_assignment_data()  # データを取得
    solve_personnel_assignment(data)  # 問題を解く