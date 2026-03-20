from flask import Blueprint, jsonify, render_template, request

from .calculations import REF_TO_MD, calculate_thread_dimensions

bp = Blueprint(
    'un_thread',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/tool-static/un_thread',
)


@bp.route('/tools/un-thread-calculator')
def page():
    return render_template('un_thread/index.html')


@bp.route('/api/tools/un-thread-calculator/thread-sizes')
def thread_sizes():
    return jsonify(REF_TO_MD)


@bp.route('/api/tools/un-thread-calculator/calculate', methods=['POST'])
def calculate():
    try:
        result = calculate_thread_dimensions(request.json)
        return jsonify(result)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400
