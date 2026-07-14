# -*- coding: utf-8 -*-
"""报价系统后端 - Flask + SQLite"""

import os
import sqlite3
import json
from flask import Flask, request, jsonify, render_template, g
from flask_cors import CORS

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.db')


# ============ 数据库 ============

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute('PRAGMA foreign_keys = ON')
    db.executescript('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            group_name TEXT NOT NULL DEFAULT '默认产品线',
            sort_order INTEGER DEFAULT 99
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            spec TEXT DEFAULT '',
            user_count TEXT DEFAULT '',
            buy_type TEXT DEFAULT '',
            retail_price TEXT DEFAULT '',
            agent_price TEXT DEFAULT '',
            server_agent TEXT DEFAULT '',
            server_retail TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        );
    ''')
    db.commit()
    db.close()


def seed_data():
    """导入示例数据"""
    db = sqlite3.connect(DB_PATH)
    db.execute('PRAGMA foreign_keys = ON')
    
    # 检查是否已有数据
    count = db.execute('SELECT COUNT(*) FROM categories').fetchone()[0]
    if count > 0:
        db.close()
        return
    
    categories = [
        ('云ERP系统', 'ERP产品线', 1),
        ('进销存系统', 'ERP产品线', 2),
        ('财务软件', '财务产品线', 3),
        ('硬件设备', '通用产品线', 4),
    ]
    
    for name, group, order in categories:
        db.execute(
            'INSERT INTO categories (name, group_name, sort_order) VALUES (?, ?, ?)',
            (name, group, order)
        )
    db.commit()
    
    # 获取分类ID
    cat_rows = db.execute('SELECT id, name FROM categories').fetchall()
    cat_map = {row[1]: row[0] for row in cat_rows}
    
    products = [
        # 云ERP系统
        ('云ERP标准版', '标准版', '1', '买断', '5880', '1750', '550', '1880', '1、买断21用户以上，每增加一个用户，零售价增加1600。2、买断用户从第二年收取服务器费用。', 1, cat_map['云ERP系统']),
        ('云ERP标准版', '标准版', '1', '年费', '2980', '850', '', '', '年费包含第一年服务器费用，次年续费按年费标准收取。', 2, cat_map['云ERP系统']),
        ('云ERP专业版', '专业版', '5', '买断', '12800', '4200', '1200', '3800', '适合中型企业，支持多仓库多门店管理。', 3, cat_map['云ERP系统']),
        ('云ERP专业版', '专业版', '5', '年费', '6800', '2100', '', '', '年费包含第一年服务器费用。', 4, cat_map['云ERP系统']),
        ('云ERP旗舰版', '旗舰版', '10', '买断', '26800', '8500', '2200', '6800', '适合大型企业，支持多组织多账套。', 5, cat_map['云ERP系统']),
        ('云ERP旗舰版', '旗舰版', '10', '年费', '13800', '4200', '', '', '年费包含第一年服务器费用。', 6, cat_map['云ERP系统']),
        
        # 进销存系统
        ('进销存普及版', 'V3', '1', '买断', '1980', '680', '', '', '适合小型商贸企业，基础进销存管理。', 1, cat_map['进销存系统']),
        ('进销存标准版', 'V3', '3', '买断', '3980', '1380', '300', '980', '适合成长型商贸企业，支持多仓库。', 2, cat_map['进销存系统']),
        ('进销存专业版', 'V3', '5', '买断', '6980', '2380', '500', '1580', '支持批次管理、保质期管理。', 3, cat_map['进销存系统']),
        ('进销存专业版', 'V3', '5', '年费', '3600', '1200', '', '', '年费包含第一年服务。', 4, cat_map['进销存系统']),
        
        # 财务软件
        ('财务标准版', 'V8', '1', '买断', '3680', '1280', '', '', '基础财务核算，适合小企业。', 1, cat_map['财务软件']),
        ('财务专业版', 'V8', '3', '买断', '7680', '2680', '400', '1280', '支持辅助核算、多币种。', 2, cat_map['财务软件']),
        ('财务旗舰版', 'V8', '10', '买断', '16800', '5800', '800', '2800', '支持集团财务、合并报表。', 3, cat_map['财务软件']),
        
        # 硬件设备
        ('条码扫描枪', '有线USB', '1', '买断', '180', '85', '', '', '通用型条码扫描枪，即插即用。', 1, cat_map['硬件设备']),
        ('标签打印机', '热敏', '1', '买断', '680', '320', '', '', '支持各种标签纸，适合仓储物流。', 2, cat_map['硬件设备']),
        ('小票打印机', '58mm', '1', '买断', '260', '120', '', '', '热敏小票打印机，带自动切刀。', 3, cat_map['硬件设备']),
        ('钱箱', '双层', '1', '买断', '220', '100', '', '', '电动钱箱，支持RS232/USB接口。', 4, cat_map['硬件设备']),
        ('PDA手持终端', '安卓', '1', '买断', '1680', '850', '', '', '安卓PDA，带条码扫描功能。', 5, cat_map['硬件设备']),
    ]
    
    for p in products:
        db.execute('''
            INSERT INTO products (product_name, spec, user_count, buy_type, retail_price, 
                agent_price, server_agent, server_retail, notes, sort_order, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', p)
    
    db.commit()
    db.close()


# ============ API 接口 ============

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin')
def admin():
    return render_template('admin.html')


# ---- 分类接口 ----

@app.route('/api/categories')
def get_categories():
    db = get_db()
    rows = db.execute('SELECT * FROM categories ORDER BY group_name, sort_order, id').fetchall()
    result = []
    for r in rows:
        result.append({
            'id': r['id'],
            'name': r['name'],
            'group_name': r['group_name'],
            'sort_order': r['sort_order']
        })
    return jsonify(result)


@app.route('/api/categories', methods=['POST'])
def add_category():
    data = request.get_json()
    db = get_db()
    try:
        db.execute(
            'INSERT INTO categories (name, group_name, sort_order) VALUES (?, ?, ?)',
            (data['name'], data.get('group_name', '默认产品线'), data.get('sort_order', 99))
        )
        db.commit()
        return jsonify({'ok': True, 'msg': '添加成功'})
    except sqlite3.IntegrityError:
        return jsonify({'ok': False, 'msg': '分类名称已存在'}), 400


@app.route('/api/categories/<int:cid>', methods=['PUT'])
def update_category(cid):
    data = request.get_json()
    db = get_db()
    db.execute(
        'UPDATE categories SET name=?, group_name=?, sort_order=? WHERE id=?',
        (data['name'], data.get('group_name', '默认产品线'), data.get('sort_order', 99), cid)
    )
    db.commit()
    return jsonify({'ok': True, 'msg': '修改成功'})


@app.route('/api/categories/<int:cid>', methods=['DELETE'])
def delete_category(cid):
    db = get_db()
    db.execute('DELETE FROM categories WHERE id=?', (cid,))
    db.commit()
    return jsonify({'ok': True, 'msg': '删除成功'})


# ---- 产品接口 ----

@app.route('/api/products')
def get_products():
    db = get_db()
    category_id = request.args.get('category_id')
    
    if category_id:
        rows = db.execute(
            'SELECT p.*, c.name as category_name, c.group_name FROM products p '
            'JOIN categories c ON p.category_id = c.id '
            'WHERE p.category_id = ? ORDER BY p.sort_order, p.id', (category_id,)
        ).fetchall()
    else:
        rows = db.execute(
            'SELECT p.*, c.name as category_name, c.group_name FROM products p '
            'JOIN categories c ON p.category_id = c.id '
            'ORDER BY c.group_name, c.sort_order, p.sort_order, p.id'
        ).fetchall()
    
    result = []
    for r in rows:
        result.append({
            'id': r['id'],
            'category_id': r['category_id'],
            'category_name': r['category_name'],
            'group_name': r['group_name'],
            'product_name': r['product_name'],
            'spec': r['spec'],
            'user_count': r['user_count'],
            'buy_type': r['buy_type'],
            'retail_price': r['retail_price'],
            'agent_price': r['agent_price'],
            'server_agent': r['server_agent'],
            'server_retail': r['server_retail'],
            'notes': r['notes'],
            'sort_order': r['sort_order'],
        })
    return jsonify(result)


@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.get_json()
    db = get_db()
    db.execute('''
        INSERT INTO products (category_id, product_name, spec, user_count, buy_type,
            retail_price, agent_price, server_agent, server_retail, notes, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['category_id'], data['product_name'], data.get('spec', ''),
        data.get('user_count', ''), data.get('buy_type', ''),
        data.get('retail_price', ''), data.get('agent_price', ''),
        data.get('server_agent', ''), data.get('server_retail', ''),
        data.get('notes', ''), data.get('sort_order', 0)
    ))
    db.commit()
    return jsonify({'ok': True, 'msg': '添加成功'})


@app.route('/api/products/<int:pid>', methods=['PUT'])
def update_product(pid):
    data = request.get_json()
    db = get_db()
    db.execute('''
        UPDATE products SET category_id=?, product_name=?, spec=?, user_count=?, buy_type=?,
            retail_price=?, agent_price=?, server_agent=?, server_retail=?, notes=?, sort_order=?
        WHERE id=?
    ''', (
        data['category_id'], data['product_name'], data.get('spec', ''),
        data.get('user_count', ''), data.get('buy_type', ''),
        data.get('retail_price', ''), data.get('agent_price', ''),
        data.get('server_agent', ''), data.get('server_retail', ''),
        data.get('notes', ''), data.get('sort_order', 0), pid
    ))
    db.commit()
    return jsonify({'ok': True, 'msg': '修改成功'})


@app.route('/api/products/<int:pid>', methods=['DELETE'])
def delete_product(pid):
    db = get_db()
    db.execute('DELETE FROM products WHERE id=?', (pid,))
    db.commit()
    return jsonify({'ok': True, 'msg': '删除成功'})


# ---- 统计接口 ----

@app.route('/api/stats')
def get_stats():
    db = get_db()
    cat_count = db.execute('SELECT COUNT(*) FROM categories').fetchone()[0]
    prod_count = db.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    group_count = db.execute('SELECT COUNT(DISTINCT group_name) FROM categories').fetchone()[0]
    return jsonify({
        'categories': cat_count,
        'products': prod_count,
        'groups': group_count
    })


if __name__ == '__main__':
    init_db()
    seed_data()
    print('数据库已初始化，示例数据已导入')
    print('前台报价系统: http://localhost:5000/')
    print('后台管理面板: http://localhost:5000/admin')
    app.run(host='0.0.0.0', port=5000, debug=True)
