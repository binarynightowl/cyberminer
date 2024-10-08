from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from os import getenv

from sqlalchemy import and_, or_, not_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = getenv("SQLALCHEMY_DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Domain(db.Model):
    __tablename__ = 'domains'
    id = db.Column(db.Integer, primary_key=True)
    domain_name = db.Column(db.Text, nullable=False)


class URL(db.Model):
    __tablename__ = 'urls'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domains.id'), nullable=False)
    path = db.Column(db.Text, nullable=False, unique=True)
    depth = db.Column(db.Integer, default=1)
    domain = db.relationship('Domain', backref=db.backref('urls', lazy=True))


class Word(db.Model):
    __tablename__ = 'words'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.Text, nullable=False)


class WordCount(db.Model):
    __tablename__ = 'word_count'
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, nullable=False)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), nullable=False)
    url_id = db.Column(db.Integer, db.ForeignKey('urls.id'), nullable=False)
    word = db.relationship('Word', backref=db.backref('word_counts', lazy=True))
    url = db.relationship('URL', backref=db.backref('word_counts', lazy=True))


@app.route('/search', methods=['POST'])
def search():
    search_term = request.json.get('search_term', '')
    search_type = request.json.get('search_type', 'OR')

    if not search_term:
        return jsonify({'error': 'No search term provided'}), 400

    search_terms = search_term.split()

    if search_type == 'AND':
        filter_condition = and_(*[Word.word.like(f'%{term}%') for term in search_terms])
    elif search_type == 'OR':
        filter_condition = or_(*[Word.word.like(f'%{term}%') for term in search_terms])
    elif search_type == 'NOT':
        filter_condition = not_(or_(*[Word.word.like(f'%{term}%') for term in search_terms]))
    else:
        return jsonify({'error': 'Invalid search type provided'}), 400

    results = db.session.query(
        db.func.sum(WordCount.count).label('count'),
        URL.path
    ).join(Word, WordCount.word_id == Word.id
           ).join(URL, WordCount.url_id == URL.id
                  ).filter(filter_condition
                           ).group_by(URL.path
                                      ).order_by(db.desc('count')
                                                 ).all()

    return jsonify([{'count': result.count, 'path': result.path} for result in results])


if __name__ == '__main__':
    app.run(debug=False)
