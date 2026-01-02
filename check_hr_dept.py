import csv

with open('./data/社員について/社員名簿.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = [row for row in reader]
    
    # 人事部の従業員を抽出
    hr_dept = [row for row in rows if row['部署'] == '人事部']
    
    print(f"人事部の従業員数: {len(hr_dept)}")
    print("\n人事部の従業員:")
    for i, row in enumerate(hr_dept, 1):
        print(f"{i}. {row['社員ID']} - {row['氏名（フルネーム）']} ({row['役職']})")
    
    # 人事管理スキルを持つ従業員を確認
    print("\n\n「人事管理」スキルを持つ従業員（全部署）:")
    hr_skill = [row for row in rows if '人事管理' in row.get('スキルセット', '')]
    for i, row in enumerate(hr_skill, 1):
        print(f"{i}. {row['社員ID']} - {row['氏名（フルネーム）']} - 部署:{row['部署']}")
