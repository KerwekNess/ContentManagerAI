from flask import Flask, jsonify, render_template, request, session
from config import Settings
from services.ai_service import AIService
from services.db_service import DBService
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'super-secret-key-for-dev')

# Initialization
try:
    settings = Settings()
    settings.validate()
    ai_service = AIService(settings)
    db_service = DBService(settings)
except Exception as e:
    print(f'Initialization Error: {e}')
    settings = None
    ai_service = None
    db_service = None

@app.route('/')
def index():
    # Теперь просто возвращаем страницу, без проверки сессии
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    if not ai_service or not db_service:
        return jsonify({'error': 'Service initialization error.'}), 500

    data = request.get_json(silent=True) or {}
    topic = data.get('topic', '').strip()
    style = data.get('style', 'expert').strip()

    if not topic:
        return jsonify({'error': 'Topic is required'}), 400

    try:
        # Запускаем Autopilot (он сам переберет модели внутри)
        result = ai_service.generate_content_pipeline(topic, style)

        db_service.save_generation(
            topic=result['topic'],
            style=result['style'],
            ideas=result['ideas'],
            post_text=result['post_text'],
            titles=result['titles'],
            hashtags=result['hashtags']
        )

        return jsonify(result)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f'Error in generation: {e}')
        return jsonify({'error': str(e)}), 502

if __name__ == '__main__':
    debug_mode = True
    if settings:
        debug_mode = settings.DEBUG
    app.run(debug=debug_mode, port=5000)
