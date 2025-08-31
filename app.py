from flask import Flask, jsonify, send_file
from werkzeug.middleware.proxy_fix import ProxyFix
from config import API_HOST, API_PORT, API_DEBUG, OUTPUT_FINAL_REPORT_EXCEL
from utils import rate_limit, TempURLManager
from storage_manager import CloudStorageManager

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

storage_manager = CloudStorageManager()
temp_url_manager = TempURLManager("salida/temp/temp_urls.json")

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/reporte-temp-url')
@rate_limit(limit=5, per=60)
def get_reporte_temp_url():
    signed_url = storage_manager.generate_signed_url("reporte_stock_hoy.xlsx", expiration_minutes=30)
    if signed_url:
        return jsonify({"url": signed_url, "expires_in": 30})
    return jsonify({"error": "No se pudo generar URL"}), 500

@app.route('/api/temp-url/<token>')
def get_file_by_temp_url(token):
    file_path = temp_url_manager.get_file_path(token)
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "URL inválida"}), 404

if __name__ == "__main__":
    app.run(host=API_HOST, port=API_PORT, debug=API_DEBUG)