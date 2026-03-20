from importlib import import_module

from flask import Flask, redirect, render_template, url_for

from tools import TOOL_REGISTRY


def _load_blueprint(import_path):
    module_path, attr = import_path.split(':', 1)
    module = import_module(module_path)
    return getattr(module, attr)


def create_app():
    app = Flask(__name__)

    for tool in TOOL_REGISTRY:
        app.register_blueprint(_load_blueprint(tool.blueprint_import))

    @app.route('/')
    def home():
        return render_template('home.html', tools=TOOL_REGISTRY)

    @app.route('/un-thread-calculator')
    def legacy_un_thread_url():
        return redirect(url_for('un_thread.page'), code=301)

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
