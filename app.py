# -*- coding: utf-8 -*-
"""人工生命WebMIDIコントローラー - Render対応版"""

import time, random, threading, os
from queue import Queue
from flask import Flask, jsonify, request
from flask_cors import CORS

# --- 🔒 セキュリティ設定 ---
SECRET_TOKEN = "mysecret123"  # HTMLと合わせる

app = Flask(__name__)
CORS(app)

# ======================================================================
# ALife音楽関数
# ======================================================================
def cellular_automaton_music(rule=110, width=64, steps=64):
    state = [0] * width
    state[width // 2] = 1
    history = [list(state)]
    for _ in range(steps - 1):
        new_state = [0] * width
        for i in range(1, width - 1):
            pattern = state[i-1] * 4 + state[i] * 2 + state[i+1]
            if (rule >> pattern) & 1:
                new_state[i] = 1
        history.append(list(new_state))
        state = new_state
    return history

def fitness(melody):
    if len(melody) < 2:
        return 0
    return -sum(abs(melody[i] - melody[i-1]) for i in range(1, len(melody)))

def mutate(melody):
    new_melody = list(melody)
    index = random.randint(0, len(new_melody) - 1)
    change = random.choice([-2, -1, 1, 2])
    new_melody[index] += change
    new_melody[index] = max(48, min(72, new_melody[index]))
    return new_melody

def evolve_one_generation(melody):
    if not melody:
        return []
    candidate = mutate(melody)
    return candidate if fitness(candidate) > fitness(melody) else melody

# ======================================================================
# Webサーバーと進化ループ
# ======================================================================
melody_queue = Queue()

def evolution_loop():
    print("\n🤖 セルオートマトンで初期メロディを生成します...")
    current_melody = [60 + int(sum(row) % 12) for row in cellular_automaton_music(rule=110)]
    generation_count = 0
    while True:
        generation_count += 1
        melody_queue.put(current_melody)
        current_melody = evolve_one_generation(current_melody)
        print(f"--- 世代 {generation_count} のメロディを生成 ---")
        time.sleep(5)

@app.route("/get_melody")
def get_melody():
    token = request.args.get("token")
    if token != SECRET_TOKEN:
        return jsonify({"error": "unauthorized"}), 403

    if not melody_queue.empty():
        return jsonify(melody_queue.get())
    else:
        return jsonify([])

# ======================================================================
# メイン処理
# ======================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🌐 Flaskサーバーを起動します... (port={port})")

    print("\n🧬 バックグラウンドで進化プロセスを開始します...")
    evolution_thread = threading.Thread(target=evolution_loop, daemon=True)
    evolution_thread.start()

    app.run(host="0.0.0.0", port=port)
