from ytb_comments import create_app

app = create_app()
with app.app_context():
    pass
#     # db.drop_all()
#     db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
