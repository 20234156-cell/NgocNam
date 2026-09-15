from fastapi.testclient import TestClient

from api.main import app


def test_saved_cases_scope_history_and_pagination(users, prime):
    officer, risk = users['officer'], users['risk']
    assert officer.get('/cases').json()['total'] == 0
    first = officer.post('/predict', json=prime).json()
    revised = {**prime, 'thu_nhap_thang_vnd': prime['thu_nhap_thang_vnd'] + 1000000}
    second = risk.post('/predict', json=revised).json()
    other = {**prime, 'ma_ho_so': 'RISK-PRIVATE'}
    assert risk.post('/predict', json=other).status_code == 200
    listing = officer.get('/cases').json()
    assert listing['total'] == 1
    assert listing['items'][0]['request_id'] == second['request_id']
    assert risk.get('/cases?limit=1').json()['total'] == 2
    assert len(risk.get('/cases?limit=1&offset=1').json()['items']) == 1
    assert risk.get('/cases?q=PRIVATE').json()['total'] == 1
    assert officer.get('/cases?q=PRIVATE').json()['total'] == 0
    assert risk.get('/cases?q=%25').json()['total'] == 0
    assert officer.get('/cases/RISK-PRIVATE/history').status_code == 403
    history = officer.get(f"/cases/{prime['ma_ho_so']}/history?limit=1").json()
    assert history['total'] == 2
    assert history['items'][0]['assessment']['request_id'] == second['request_id']
    older = officer.get(f"/cases/{prime['ma_ho_so']}/history?limit=1&offset=1").json()['items'][0]['assessment']
    assert older['request_id'] == first['request_id']
    assert older['application_snapshot']['thu_nhap_thang_vnd'] == prime['thu_nhap_thang_vnd']
    assert 'ho_ten' not in older
    assert officer.get('/cases/UNKNOWN/history').status_code == 404
    assert officer.get('/cases?limit=101').status_code == 422
    with TestClient(app) as anonymous:
        assert anonymous.get('/cases').status_code == 401
        assert anonymous.get(f"/cases/{prime['ma_ho_so']}/history").status_code == 401
