from flask import Flask, request, render_template_string, redirect, url_for, flash
import pickle
import requests
import certifi

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a strong secret key

# Load your data (ensure these files are in the same directory)
movies = pickle.load(open('movie_list.pkl', 'rb'))
with open('similarity.pkl', 'rb') as file:
    similarity = pickle.load(file)

movie_list = movies['title'].values.tolist()


def fetch_poster(movie_id):
    API_KEY = "7a30e255cc19e74a0573c9b8c6c960bd"
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"

    session = requests.Session()  # Use a session for better performance
    adapter = requests.adapters.HTTPAdapter(max_retries=3)
    session.mount("https://", adapter)

    try:
        response = session.get(url, timeout=5, verify=certifi.where())
        response.raise_for_status()
        data = response.json()
        poster_path = data.get("poster_path")
        return f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

    except requests.exceptions.SSLError:
        print("SSL Error: Retrying without SSL verification...")
        response = session.get(url, timeout=5, verify=False)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get("poster_path")
        return f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

    except requests.exceptions.RequestException as e:
        print("API request failed:", e)
        return None


def recommend(movie):
    try:
        index = movies[movies['title'] == movie].index[0]
    except IndexError:
        return []

    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommendations = []

    for i in distances[1:6]:
        try:
            movie_id = movies.iloc[i[0]].movie_id
            poster = fetch_poster(movie_id)
            if poster:
                recommendations.append((movies.iloc[i[0]].title, poster))
        except Exception as e:
            print(f"Error fetching details for movie ID {movie_id}: {e}")

    return recommendations



TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Movie Recommender System</title>
    
    <style>

        body {
            background-color: #000000 !important;
            color: #ffffff !important;
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 0;
        }
        .container {
            width: 90%;
            margin: auto;
            padding: 20px;
        }
        h1 {
            text-align: center;
            font-size: 3rem;
            color: #1DB954;  
            font-weight: bold;
            text-shadow: 2px 2px 10px rgba(29, 185, 84, 0.8);
            animation: fadeIn 2s ease-in-out;
        }
        form {
            text-align: center;
            margin-bottom: 30px;
        }
        label {
            font-size: 1.2rem;
            display: block;
            margin-bottom: 10px;
            color: white;
        }
        select {
            background-color: #222;
            color: white;
            border-radius: 10px;
            padding: 10px;
            font-size: 1rem;
            margin-bottom: 20px;
        }
        input[type="submit"] {
            background: linear-gradient(45deg, #1DB954, #17a743);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            padding: 10px 15px;
            transition: transform 0.3s ease, background 0.3s ease;
            box-shadow: 0 4px 10px rgba(29,185,84,0.8);
            cursor: pointer;
        }
        input[type="submit"]:hover {
            transform: scale(1.1);
            background: linear-gradient(45deg, #17a743, #1DB954);
        }
        .recommendation-container {
            text-align: center;
            animation: fadeIn 2s ease-in-out;
        }
        .movie-card {
            display: inline-block;
            margin: 10px;
            text-align: center;
        }
        .movie-card img {
            border-radius: 15px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            box-shadow: 0 4px 10px rgba(255, 255, 255, 0.2);
            width: 200px;
            height: auto;
            animation: fadeIn 2s ease-in-out;
        }
        .movie-card img:hover {
            transform: scale(1.1);
            box-shadow: 0 8px 20px rgba(255, 255, 255, 0.8);
        }
        .movie-title {
            font-size: 1.2rem;
            font-weight: bold;
            margin-top: 10px;
            color: white;
            text-shadow: 1px 1px 5px rgba(0, 0, 0, 0.8);
            animation: fadeIn 2s ease-in-out;
        }
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(-10px); }
            100% { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Movie Recommender System</h1>
        <form method="post">
            <label for="movie">Type or select a movie from the dropdown</label>
            <select name="movie" id="movie">
                {% for movie in movie_list %}
                    <option value="{{ movie }}" {% if movie == selected_movie %}selected{% endif %}>{{ movie }}</option>
                {% endfor %}
            </select><br>
            <input type="submit" value="Show Recommendation">
        </form>

        {% if recommendations %}
        <div class="recommendation-container">
            {% for title, poster in recommendations %}
                <div class="movie-card">
                    <div class="movie-title">{{ title }}</div>
                    <img src="{{ poster }}" alt="{{ title }} Poster">
                </div>
            {% endfor %}
        </div>
        {% elif selected_movie %}
            <p style="text-align:center;">No recommendations found.</p>
        {% endif %}
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    selected_movie = None
    recommendations = None
    if request.method == "POST":
        selected_movie = request.form.get("movie")
        if selected_movie:
            recommendations = recommend(selected_movie)
            if not recommendations:
                flash("No recommendations found for the selected movie.", "warning")
    return render_template_string(TEMPLATE, movie_list=movie_list, selected_movie=selected_movie,
                                  recommendations=recommendations)


if __name__ == "__main__":
    app.run(debug=True)
