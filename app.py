"""
app.py - Main Flask Application Server
======================================
Serves:
1. Student Chatbot Web Interface (/)
2. Administrative FAQ & Query Management Portal (/admin)
3. RESTful API endpoints for chat interactions and data management
"""

import os
from flask import Flask, render_template, request, jsonify
from database import (
    init_db,
    get_all_faqs,
    get_faq_by_id,
    add_faq,
    update_faq,
    delete_faq,
    search_faqs,
    log_query,
    get_query_logs,
    get_unanswered_queries,
    get_stats
)
from chatbot import chatbot_engine

app = Flask(__name__)
app.config['SECRET_KEY'] = 'college-chatbot-secret-key-2026'

# Ensure database tables exist and are populated with initial FAQs
init_db()


# ==============================================================================
# FRONTEND ROUTES
# ==============================================================================

@app.route('/')
def home():
    """Render the main student chatbot interface."""
    return render_template('index.html')


@app.route('/admin')
def admin_portal():
    """Render the administrative FAQ and log management dashboard."""
    stats = get_stats()
    faqs = get_all_faqs()
    unanswered = get_unanswered_queries(limit=20)
    logs = get_query_logs(limit=30)
    return render_template('admin.html', stats=stats, faqs=faqs, unanswered=unanswered, logs=logs)


# ==============================================================================
# CHATBOT API ENDPOINTS
# ==============================================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Primary chat endpoint.
    Receives user query, predicts intent, logs interaction, and returns response.
    """
    try:
        data = request.get_json(silent=True) or {}
        user_message = data.get('message', '').strip()

        # Input validation
        if not user_message:
            return jsonify({
                "success": False,
                "response": "Please type a question before sending.",
                "intent": "empty_input",
                "confidence": 0.0,
                "is_fallback": True,
                "suggestions": ["Admission Process", "Courses Offered", "Fee Structure", "Contact Details"]
            }), 400

        # Process through NLP Chatbot Engine
        result = chatbot_engine.get_response(user_message)

        # Log query in database for analytics & admin review
        log_query(
            user_query=user_message,
            matched_intent=result['intent'],
            confidence=result['confidence'],
            is_fallback=result['is_fallback']
        )

        return jsonify({
            "success": True,
            "response": result['response'],
            "intent": result['intent'],
            "confidence": result['confidence'],
            "is_fallback": result['is_fallback'],
            "suggestions": result.get('suggestions', [])
        })

    except Exception as e:
        app.logger.error(f"Chat endpoint error: {e}")
        return jsonify({
            "success": False,
            "response": "An internal error occurred while processing your request. Please try again.",
            "intent": "error",
            "confidence": 0.0,
            "is_fallback": True,
            "suggestions": ["Admission Process", "Contact Details"]
        }), 500


@app.route('/api/faqs', methods=['GET'])
def get_faqs_api():
    """Return all FAQs in JSON format."""
    faqs = get_all_faqs()
    return jsonify({"success": True, "faqs": faqs})


# ==============================================================================
# ADMINISTRATIVE API ENDPOINTS
# ==============================================================================

@app.route('/api/admin/faq', methods=['POST'])
def add_faq_api():
    """Add a new FAQ to the SQLite database."""
    try:
        data = request.get_json(silent=True) or request.form
        category = data.get('category', '').strip()
        question = data.get('question', '').strip()
        answer = data.get('answer', '').strip()
        keywords = data.get('keywords', '').strip()

        if not category or not question or not answer:
            return jsonify({"success": False, "message": "Category, question, and answer are required."}), 400

        faq_id = add_faq(category, question, answer, keywords)
        return jsonify({"success": True, "message": "FAQ added successfully!", "faq_id": faq_id})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/admin/faq/delete/<int:faq_id>', methods=['POST', 'DELETE'])
def delete_faq_api(faq_id):
    """Delete an FAQ by ID."""
    try:
        success = delete_faq(faq_id)
        if success:
            return jsonify({"success": True, "message": "FAQ deleted successfully."})
        return jsonify({"success": False, "message": "FAQ not found."}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/admin/stats', methods=['GET'])
def stats_api():
    """Return dashboard analytics summary."""
    return jsonify({"success": True, "stats": get_stats()})


# ==============================================================================
# ERROR HANDLERS
# ==============================================================================

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html'), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "error": "Internal Server Error"}), 500


if __name__ == '__main__':
    print("=" * 65)
    print("  AI CHATBOT FOR COLLEGE ENQUIRIES - FLASK SERVER")
    print("  Local Server Address: http://127.0.0.1:5000")
    print("  Admin Dashboard:     http://127.0.0.1:5000/admin")
    print("=" * 65)
    app.run(host='127.0.0.1', port=5000, debug=True)

