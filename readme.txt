To run this project Movie_Recommendation:


1) Clone this project with 'https' url
2) Create virtual environment as 'movie_env' using python command as:
    python -m venv movie_env
3) Now, install the requirements using python command as:
    pip install -r requirements.txt
    [Note: requirements.txt file is inside 'Movie' directory]

4) Create MySQL database with database name as 'movie'.
5) Create 'config.json' file inside 'Movie' and paste below code:
      {
      "DEFAULT":
      {
        "DATABASE_USER": "root",
        "DATABASE_PASS": "",
        "DATABASE_NAME": "Movie",
        "EMAIL_HOST_USER": "",
        "EMAIL_HOST_PASSWORD": "",
        "EMAIL_HOST": "smtp.gmail.com",
        "EMAIL_PORT": "587"
      }
    }
6) After that run the setup command as:
    python manage.py setup

7) You also need to have 'media' file which is in 'https://drive.google.com/drive/folders/1jqaHaPcCmXIFOKpbLfj2LWaKgrrGwdAg?usp=drive_link'
8) You need 'item_similarty_df.csv' file as well which is in 'https://drive.google.com/file/d/1wPav1d9uBN_mKvtkamd-KdKzNcMwRfoO/view?usp=drive_link'
