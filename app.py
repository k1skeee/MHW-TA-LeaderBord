from flask import Flask, render_template, request, session, redirect, url_for
import pandas as pd

app = Flask(__name__)

# --- セキュリティ設定 ---
# セッションの暗号化キーです。
app.secret_key = 'mhw_ta_leaderboard_secret_key_2026'
# 管理用パスワード
ADMIN_PASSWORD = "2580"

# スプレッドシートのCSV URL
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcMMQrQ8HJdyuVQNl4h335dlBV7KDsKZJhAorHagNy-KIBbuH9X_UB7bgM26WVevVqw0tz0yZj3a9X/pub?gid=0&single=true&output=csv"

# クエストデータ 
quests = [
    {'id': 'milla', 'name': 'M6★ Fade to Black', 'target': 'Fatalis', 'display_name': 'Fatalis', 'icon': 'ミラボレアス.PNG'},
    {'id': 'velkhana', 'name': 'M6★ The Place Where Winter Sleeps', 'target': 'AT Velkhana', 'display_name': 'AT Velkhana', 'icon': '歴戦王イヴェルカーナ.PNG'},
    {'id': 'rajang', 'name': 'M6★ Mew are Number One!', 'target': 'Furious Rajang', 'display_name': 'Furious Rajang', 'icon': '激昂したラージャン.PNG'},
    {'id': 'alatreon_fire', 'name': 'M6★ The Evening Star', 'target': '宵Alatreon', 'display_name': 'Alatreon', 'icon': 'アルバトリオン.PNG'},
    {'id': 'alatreon_ice', 'name': 'M6★ Dawn of The Death Star', 'target': '明Alatreon', 'display_name': 'Alatreon', 'icon': 'アルバトリオン.PNG'},
    {'id': 'negi', 'name': 'M6★ Ode to the Destruction', 'target': 'Nergigante', 'display_name': 'Ruiner Nergigante', 'icon': 'ネルギガンテ.PNG'},
]

def get_records_from_sheet():
    try:
        # 毎回最新のデータを読み込む
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.str.strip()
        df = df.fillna('')  # 空白セルを空文字で埋める
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"スプレッドシート読み込みエラー: {e}")
        return []

# ログイン処理用のルーティング
@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ADMIN_PASSWORD:
        session['logged_in'] = True
        session.permanent = True  # ブラウザを閉じても一定期間ログインを維持
        return redirect(url_for('index'))
    else:
        # 【修正箇所】パスワードが違う場合も、HTMLが必要とする変数をすべて渡してエラーを防ぐ
        return render_template(
            'index.html', 
            show_login=True, 
            error="Invalid Password",
            quests=quests,
            selected_quest=quests[0],
            active_tab='quest'
        )

# ログアウト処理用のルーティング
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/')
def index():
    # --- 認証チェック ---
    if not session.get('logged_in'):
        # 未ログイン時でも、画面描画（JSの初期化等）に必要な変数をすべて渡す
        return render_template(
            'index.html', 
            show_login=True, 
            quests=quests, 
            selected_quest=quests[0], # デフォルトのクエストを渡しておく
            active_tab='quest'        # デフォルトのタブを指定しておく
        )

    # --- 以下、ログイン済みの場合のみ実行される既存ロジック ---
    all_records = get_records_from_sheet()
    
    # URLパラメータの取得（タブ切り替えや検索条件）
    active_tab = request.args.get('tab', 'quest')
    selected_id = request.args.get('monster', 'milla')
    sel_weapon = request.args.get('weapon', 'All')
    sel_style = request.args.get('style', 'All')
    sel_platform = request.args.get('platform', 'All')

    # 選択されたモンスターの情報を取得
    selected_quest = next((q for q in quests if q['id'] == selected_id), quests[0])

    # --- フィルタリング処理 ---
    # 1. まずターゲットで絞り込み
    filtered = [r for r in all_records if str(r.get('target')).strip() == selected_quest['target']]
    
    # 2. 武器で絞り込み
    if sel_weapon != 'All':
        filtered = [r for r in filtered if str(r.get('weapon')).strip() == sel_weapon]
        
    # 3. プラットフォームで絞り込み (Unknown救済対応済み)
    if sel_platform != 'All':
        filtered = [
            r for r in filtered 
            if str(r.get('platform')).strip() == sel_platform 
            or str(r.get('platform')).strip() == 'Unknown'
        ]
        
    # 4. スタイルで絞り込み
    if sel_style != 'All':
        filtered = [r for r in filtered if str(r.get('style')).strip() == sel_style]

    # タイム順にソート (未入力は後ろへ)
    filtered.sort(key=lambda x: str(x.get('time', '99:59:59')))

    return render_template('index.html', 
                           show_login=False,
                           quests=quests, 
                           selected_quest=selected_quest, 
                           records=filtered,
                           active_tab=active_tab,
                           sel_weapon=sel_weapon, 
                           sel_platform=sel_platform, 
                           sel_style=sel_style)

if __name__ == '__main__':
    # 外部アクセス許可設定
    app.run(host='0.0.0.0', port=5000, debug=True)