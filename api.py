from flask import Blueprint, request, jsonify
from flask_login import login_required
from database import get_connection

api = Blueprint('api', __name__)


@api.route('/api/dashboard/Sume', methods=['GET'])
@login_required
def get_summary():
    # print("TEEEEEEEEEEEEEEEEEEEEEEESTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT")
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    querry = """
        SELECT
            SUM(Consum_kWh) AS total_consum,
            AVG(Consum_kWh) AS mediu_consum
        FROM consum_energie
        WHERE DataCitire BETWEEN %s AND %s
    """
    cursor.execute(querry, (start_date, end_date))
    result = cursor.fetchone()

    cursor.close()
    conn.close()
    return jsonify(result)


@api.route('/api/dashboard/top5', methods=['GET'])
@login_required
def get_top_consumatori():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT ClientID, SUM(Consum_kWh) AS total
    FROM consum_energie
    WHERE DataCitire BETWEEN %s AND %s
    GROUP BY ClientID
    ORDER BY total DESC
    LIMIT 5
"""
    cursor.execute(query, (start_date, end_date))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results)


@api.route('/api/dashboard/defect', methods=['GET'])
@login_required
def get_alerte():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT c.ClientID
        FROM consum_energie c
        JOIN consum_energie s ON s.ClientID = c.ClientID
        WHERE s.StatusContor = 'defect'
    """
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results)


@api.route('/api/client/<int:client_id>', methods=['GET'])
@login_required
def get_client_details(client_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        'Select ClientID,Locatie,StatusContor,TipClient FROM consum_energie WHERE ClientID = %s LIMIT 1', (client_id,))
    client = cursor.fetchone()
    cursor.close()
    conn.close()
    if client:
        return jsonify(client)
        return jsonify({'error': 'Clientul nu exista'}), 404


@api.route('/api/consum_energie', methods=['GET'])
@login_required
def get_consum_energie():
    client_id = request.args.get('client_id')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if client_id:
        cursor.execute(
            "SELECT * FROM consum_energie WHERE ClientID = %s", (client_id,))
    else:
        cursor.execute("SELECT * FROM consum_energie")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)


@api.route('/api/consum_energie/<int:id>', methods=['PUT'])
@login_required
def update_consum_energie(id):
    data = request.json
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE consum_energie SET 
            ClientID=%s, Locatie=%s, StatusContor=%s, TipClient=%s, Consum_kWh=%s, DataCitire=%s
        WHERE id=%s
    """, (
        data['ClientID'], data['Locatie'], data['StatusContor'], data['TipClient'],
        data['Consum_kWh'], data['DataCitire'], id
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})


@api.route('/api/client/<int:client_id>/consum', methods=['GET'])
@login_required
def api_client_consum(client_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DataCitire, Consum_kWh
        FROM consum_energie
        WHERE ClientID = %s
        ORDER BY DataCitire ASC
    """, (client_id,))
    consum = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(consum)


@api.route('/api/client/<int:client_id>/statistici', methods=['GET'])
@login_required
def api_client_statistici(client_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT AVG(Consum_kWh) AS consum_mediu,
               MAX(Consum_kWh) AS consum_maxim,
               MIN(Consum_kWh) AS consum_minim
        FROM consum_energie
        WHERE ClientID = %s
    """, (client_id,))
    stats = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(stats)
