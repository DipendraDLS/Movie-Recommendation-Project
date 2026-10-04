from django.contrib import messages  # django le diyeko inbuilt messages featueres lai import gareko
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, get_object_or_404, redirect
import json                           # yedi request ma json object aai rako cha vani.. so json data lai django view ma access garna ko lagi import json lekhna parcha

from django.http import Http404, HttpResponseForbidden

from .models import *
from login_signup.forms import CreateClientForm, CreateAdminForm, ImageUploadForm
from recommendation.models import User
from recommendation.models import Movie
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .filters import MovieFilter

from django.core.cache import cache
import pandas as pd
import numpy as np


import sweetify
from .forms import RatingForm
from django.http import JsonResponse

import feather
import time
from django.views.decorators.cache import cache_page



# Create your views here.

# @login_required
def upload_pic(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            m = User.objects.get(id=request.user.id)
            m.image = form.cleaned_data['image']
            m.save()
            if request.user.is_admin:
                return redirect('adminhome')
            else:
                return redirect('clienthome')
    return HttpResponseForbidden('Choose the photo first. Allowed only via POST')





def filtermovie(request):

    genre = request.POST.get('genre')
    year = request.POST.get('year')
    imdb_rating = request.POST.get('imdbrating')


    if request.method == 'POST':

        if genre == '' and year == '' and imdb_rating == '':

            myFilter = MovieFilter()
            return render(request, 'recommendation/filtermovies.html', {'myFilter': myFilter})


        movies_all = Movie.objects.all()


        myFilter = MovieFilter(request.POST, queryset=movies_all)

        movies_all = myFilter.qs

        page = request.GET.get('page', 1)
        paginator = Paginator(movies_all, 108)
        try:
            movies = paginator.page(page)
        except PageNotAnInteger:
            movies = paginator.page(1)
        except EmptyPage:
            movies = paginator.page(paginator.num_pages)

        context = {'movies': movies, 'myFilter': myFilter}
        return render(request, 'recommendation/filtermovies.html', context)





    myFilter = MovieFilter()
    return render(request, 'recommendation/filtermovies.html', {'myFilter': myFilter})




# Rating Movies
def rate_movie(request, movie_id):



    if request.method == "POST":
        rating = request.POST.get('rating')

        # 'try' vaneko yedi user le particular movie lai feri rating dindai cha vaney yo run huncha
        try:
            clientObject = Client.objects.get(Q(user_id=request.user.id) & Q(movie_id=movie_id))
            form = RatingForm(request.POST or None, instance=clientObject)

            if rating != '0':
                edit = form.save(commit=False)
                edit.save()
                return JsonResponse({'status': 'true'}, status=200, safe=False)

        # 'except' vaneko yedi user new user ho and movie lai  first time rating dindai cha vaney yo run huncha
        except:
            form = RatingForm(request.POST)
            if rating != '0':
                form.save()
                return JsonResponse({'status':'true'}, status=200,  safe=False)


        return JsonResponse({'status':'false'}, status=400,  safe=False)





# detail definition is related with engine definition..
@cache_page(360 * 2)
def detail(request,  movie_id, user_id=None):
    # start= time.time()
    movies = get_object_or_404(Movie, id=movie_id)


    year = movies.year
    genre = movies.genre
    title = movies.title
    rate = 5
    movies_list = engine(title, rate)  #General movie recommendation ko lagi recommendation engine() function lai call gareko


    recommended_movies = list()


    try:
        for i in range(len(movies_list)):
            try:
                queryset_movie = Movie.objects.filter(Q(title=movies_list[i]))  # loop use garera i.e 0-> 9 times loop chalayera movie_list ma aako movie lai use garayera query chalako
                recommended_movies += queryset_movie  # queryset_movie vanni queryset lai recommended_movies vanni list ma add gareko

                # manually merge garna pani sakincha ..  recommended_movies = movie1 | movie2 | movie3 | movie4 | movie5 | movie6 | movie7 | movie8 | movie9 | movie10			# Merging above 4 multiple querysets to single recommended_movies queryset

                if len(recommended_movies) >= 6:
                    break

            except:
                continue

        # end = time.time()
        # print(f'Execution time taken by {title} detail page to execute : ', (end - start), 'seconds(s).')

        context = {'movies': movies, 'recommended_movies': recommended_movies}
        return render(request, 'recommendation/detail.html', context)


    except:
        # *********** Solving Cold Start Problem for Genreal Recommendation ****************************
        # best_fetched = Movie.objects.filter(genre=genre, year__range=(year - 7, year + 1)).exclude(Q(id=movie_id))
        #
        # if best_fetched.count() >= 6:
        #     recommended_movies = best_fetched
        # else:
        #     genre = genre.split(' ')
        #
        #     try:
        #         genre = genre[0] + " " + genre[1]
        #         best_fetched = Movie.objects.filter(genre=genre, year__range=(year - 10, year - 1)).exclude(
        #             Q(id=movie_id))
        #
        #         if best_fetched.count() >= 6:
        #             recommended_movies = best_fetched
        #         else:
        #             genre = genre.split(' ')
        #             genre = genre[0]
        #             best_fetched = Movie.objects.filter(genre=genre, year__range=(year - 11, year - 4)).exclude(
        #                 Q(id=movie_id))
        #
        #             if best_fetched.count() >= 6:
        #                 recommended_movies = best_fetched
        #             else:
        #                 normal_fetched = Movie.objects.filter(Q(genre=genre)).exclude(Q(id=movie_id))
        #                 recommended_movies = normal_fetched
        #
        #     except:
        #
        #         genre = genre[0]
        #         best_fetched = Movie.objects.filter(genre=genre, year__range=(year - 11, year - 4)).exclude(
        #             Q(id=movie_id))
        #
        #         if best_fetched.count() >= 6:
        #             recommended_movies = best_fetched
        #         else:
        #             normal_fetched = Movie.objects.filter(Q(genre=genre)).exclude(Q(id=movie_id))
        #             recommended_movies = normal_fetched


        context = {'movies': movies, 'recommended_movies': recommended_movies}
        return render(request, 'recommendation/detail.html', context)


# engine definition vaneko just for 'general recommendation' ko lagi and this is related with 'detail' definition
def engine(title, rate):
    name = []
    rating = []

    name.append(title)
    rating.append(rate)


#################### Yaha vanda Talako  code CSV File Nabneko And hamiley 'item_similarity_df' dataframe banauna parni ######################

    # ratings = pd.read_csv('ratings.csv')
    # movies = pd.read_csv('movies.csv')
    #
    # ratings = pd.merge(movies, ratings).drop(['genres', 'timestamp'], axis=1)  # hamile garna lageko collaborative filtering chai user ko rating ko basis ma ho.. so hamilai genres and timestamp column ko khassai use nahune vayera.. tyo columns lai drop gareko ho
    #
    # user_ratings = ratings.pivot_table(index=['userId'], columns=['title'], values='rating')
    #
    # ## Let's Remove Movies which have less than 10 users who rated it. and fill remaining NaN with 0
    # user_ratings = user_ratings.dropna(thresh=3, axis=1).fillna(0)  # dropna(thresh=10,axis=1) --> yesko kaam vaneko,  jun column (i.e movie) ma 10 vanda kam users le rating deko xa.. testo column (axis=1 vannale column bujinxa) lai drop gar vaneko  & again,  fillna(0) ko kaam vaneko column drop gari sake paxi jati column bachxa .. bacheko column ma pani NaN value tw huna saki halxa.. so tyo NaN value lai 0 le replace garni vaneko... hamile Toy dataset ma 0 re place gare jastai ho
    #
    # ## Let's Build our Similarity Matrix
    # item_similarity_df = user_ratings.corr(method='pearson')  # Applying Pearson Correlation method    # Toy dataset ma cosine similarity use garda .. standardize method use garera 0 value lai hatauna ko lagi jasto chai yo Pearson Correlation ma garna pardaina.. i.e Pearson correlation method le automatically adjust for the mean.. so we dont have to apply our standardize method over here...




############################# hamiley 'item_similarity_df' dataframe banauna parni code chai sakyo hai ava ##############################


# DataFrame lai Pickle File ma Write garney Code
    # item_similarity_df.to_pickle('item_similarity_df.pkl')


    item_similarity_df = cache.get('cleaned_data')
    if item_similarity_df is None:
        item_similarity_df = feather.read_dataframe('item_similarity_df.feather')
        item_similarity_df.index = item_similarity_df.columns
        cache.set('cleaned_data', item_similarity_df, timeout=36000)





    movielist = []

    try:
        def get_similar_movies(movie_name, user_rating):


            user_rating = float(user_rating)  # get_similar_movies() vanni chai method ho which accepts movie name ans user rating as parameters

            similar_score = item_similarity_df[movie_name] * (user_rating - 2.5)
            similar_score = similar_score.sort_values(ascending=False)

            return similar_score  # get_similar_movies()  method return similar_score or similar movies

        def check_seen(movie, seen_movies):
            for item in seen_movies:
                if item == movie:
                    return True

            return False

        similar_movies = pd.DataFrame()  # Empty datafram banayeko

        length = len(name)

        for i in range(0, length):
            similar_movies = similar_movies.append(get_similar_movies(name[i], rating[i]), ignore_index=True)
        all_recommend = similar_movies.sum().sort_values(ascending=False)



        i = 0
        for movie, score in all_recommend.iteritems():
            if not check_seen(movie, name):
                movielist.append(movie)

            i = i + 1
            if i >= 36 + length:
                break

        return movielist


    except:
        return movielist
















# sugesstion definition is related with 'myengine' definition
@login_required
def suggestion(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_active:
        raise Http404
    clients = Client.objects.filter(Q(user=request.user)).filter(Q(rating__gte=0.1)).order_by('-id')[:10]  # client table bata particular user ko latest 10 wota record nikaleko becz particular userko lagi suggested number of movies constant number rahos and yo garna le suggestion pani dynamic vayerako huncha....
    movie_id = []
    title = []
    rate = []
    genre = []
    year = []

    suggested_movies = list()

    try:
        for client in clients:
            movie_id.append(client.movie_id)
            title.append(client.movie.title)
            rate.append(client.rating)
            genre.append(client.movie.genre)
            year.append(client.movie.year)

        movies_list = myengine(movie_id, title, rate, genre, year)



        for i in range(len(movies_list)):
            queryset_movie_suggestion = Movie.objects.filter(Q(title=movies_list[i]))
            suggested_movies += queryset_movie_suggestion


            # merge manually yesri ni garna milcha ... suggested_movies = movie1 | movie2 | movie3 | movie4 | movie5 | movie6 | movie7 | movie8 | movie9 | movie10 | movie11 | movie12 | movie13 | movie14 | movie15 | movie16 | movie17 | movie18 | movie19 | movie20 | movie21 | movie22 | movie23 | movie24 | movie25 | movie26 | movie27 | movie28 | movie29 | movie30 | movie31 | movie32 | movie33 | movie34 | movie35 | movie36 | movie37 | movie38 | movie39 | movie40 | movie41 | movie42 | movie43 | movie44 | movie45 | movie46 | movie47 | movie48 | movie49 | movie50			# Merging above 4 multiple querysets to single recommended_movies queryset

    except:
        pass

    context = {'suggested_movies': suggested_movies}
    return render(request, 'recommendation/suggestion.html', context)




# myengine definition vaneko user le rating diye sakey pachi tyo user lai aauni recommended movie ko lagi ho.. and this is related with 'suggestion' definition.
def myengine(movie_id, name, rating, genre, year):


#################### Yaha vanda Talako  code CSV File Nabneko And hamiley 'item_similarity_df' dataframe banauna parni ######################

    # ratings = pd.read_csv('ratings.csv')
    # movies = pd.read_csv('movies.csv')
    #
    # ratings = pd.merge(movies, ratings).drop(['genres', 'timestamp'], axis=1)  # hamile garna lageko collaborative filtering chai user ko rating ko basis ma ho.. so hamilai genres and timestamp column ko khassai use nahune vayera.. tyo columns lai drop gareko ho
    #
    # user_ratings = ratings.pivot_table(index=['userId'], columns=['title'], values='rating')
    #
    # ## Let's Remove Movies which have less than 10 users who rated it. and fill remaining NaN with 0
    # user_ratings = user_ratings.dropna(thresh=3, axis=1).fillna(0)  # dropna(thresh=10,axis=1) --> yesko kaam vaneko,  jun column (i.e movie) ma 10 vanda kam users le rating deko xa.. testo column (axis=1 vannale column bujinxa) lai drop gar vaneko  & again,  fillna(0) ko kaam vaneko column drop gari sake paxi jati column bachxa .. bacheko column ma pani NaN value tw huna saki halxa.. so tyo NaN value lai 0 le replace garni vaneko... hamile Toy dataset ma 0 re place gare jastai ho
    #
    # ## Let's Build our Similarity Matrix
    # item_similarity_df = user_ratings.corr(method='pearson')  # Applying Pearson Correlation method    # Toy dataset ma cosine similarity use garda .. standardize method use garera 0 value lai hatauna ko lagi jasto chai yo Pearson Correlation ma garna pardaina.. i.e Pearson correlation method le automatically adjust for the mean.. so we dont have to apply our standardize method over here...



############################# hamiley 'item_similarity_df' dataframe banauna parni code chai sakyo hai ava ##############################

# DataFrame lai Pickle File ma Write garney Code
    # item_similarity_df.to_pickle('item_similarity_df.pkl')

    item_similarity_df = cache.get('cleaned_data')
    if item_similarity_df is None:
        item_similarity_df = feather.read_dataframe('item_similarity_df.feather')
        item_similarity_df.index = item_similarity_df.columns
        cache.set('cleaned_data', item_similarity_df, timeout=36000)



    movielist = []

    temp_movie_id = []
    temp_movie_name = []
    temp_movie_genre = []
    temp_movie_year = []
    try:
        def get_similar_movies(movie_name, user_rating):  # get_similar_movies() vanni chai method ho which accepts movie name and user rating as parameters
            user_rating = float(user_rating)
            similar_score = item_similarity_df[movie_name] * (user_rating - 2.5)  # item_similarty_df ma vako -ve rating lai ni as a +ve rating treat garna '-2.5' gareko.
            similar_score = similar_score.sort_values(ascending=False)


            return similar_score  # get_similar_movies()  method return similar_score or similar movies

        def check_seen(movie, seen_movies):
            for item in seen_movies:
                if item == movie:
                    return True

            return False


        length = len(name)

        cold_recommended_movies = []



        all_movies = Movie.objects.all()

        all_movies_list = []

        for movie in all_movies:
            all_movies_list.append(movie.title)


        all_recommended_movies = []
        for i in range(0, length):
            try:
                temp_recommended_movie_list = []
                all_suggested_movies = get_similar_movies(name[i], rating[i])
                temp_recommended_movie_list = list(all_suggested_movies.index)




                if rating[i] == 5.0:
                    for j in range(1, len(temp_recommended_movie_list)):
                        if temp_recommended_movie_list[j] in all_movies_list:
                            all_recommended_movies.append(temp_recommended_movie_list[j])

                        if len(all_recommended_movies) >= 6 * (i+1):
                            break


                elif rating[i] == 4.0:
                    count = 0
                    for j in range(len(temp_recommended_movie_list)):

                        if temp_recommended_movie_list[j] in all_movies_list:
                            count +=1
                            if count >= 8:
                                all_recommended_movies.append(temp_recommended_movie_list[j])

                        if len(all_recommended_movies) >= 6 * (i + 1):
                            break



                elif rating[i] == 3.0:
                    count = 0
                    for j in range(len(temp_recommended_movie_list)):

                        if temp_recommended_movie_list[j] in all_movies_list:
                            count += 1
                            if count >= 14:
                                all_recommended_movies.append(temp_recommended_movie_list[j])

                        if len(all_recommended_movies) >= 6 * (i + 1):
                            break




                elif rating[i] == 2.0:
                    count = 0
                    for j in range(len(temp_recommended_movie_list)):

                        if temp_recommended_movie_list[j] in all_movies_list:
                            count += 1
                            if count >= 7:
                                all_recommended_movies.append(temp_recommended_movie_list[j])

                        if len(all_recommended_movies) >= 6 * (i + 1):
                            break


                elif rating[i] == 1.0:
                    for j in range(0, len(temp_recommended_movie_list)):
                        if temp_recommended_movie_list[j] in all_movies_list:
                            all_recommended_movies.append(temp_recommended_movie_list[j])

                        if len(all_recommended_movies) >= 6 * (i+1):
                            break



            except:  # user le rating diyeko movie ko lagi recommendation ayena vani exception ma auncha ..

                # temp_movie_id.append(movie_id[i])
                # temp_movie_name.append(name[i])
                # temp_movie_genre.append(genre[i])
                # temp_movie_year.append(year[i])

                pass



        # *********** Solving Cold Start Problem for Rated Movies ****************************
        # if temp_movie_name:  # if condition le 'exception handling' ko kam garirako cha..
        #
        #     for i in range(0, len(temp_movie_name)):
        #         best_fetched = Movie.objects.filter(genre=temp_movie_genre[i], year__range=(
        #         temp_movie_year[i] - 7, temp_movie_year[i] + 1)).exclude(Q(id=temp_movie_id[i]))[:7]
        #
        #         if best_fetched.count() >= 6:
        #             temp_cold_movies = best_fetched
        #
        #
        #         else:
        #
        #             temp_movie_genre = temp_movie_genre[i].split(' ')
        #
        #             try:
        #
        #                 temp_movie_genre = temp_movie_genre[0] + " " + temp_movie_genre[1]
        #
        #                 temp_cold_movies = Movie.objects.filter(genre=temp_movie_genre, year__range=(
        #                 temp_movie_year[i] - 10, temp_movie_year[i] - 1)).exclude(Q(id=temp_movie_id[i]))
        #
        #                 if temp_cold_movies.count() >= 6:
        #                     temp_cold_movies = best_fetched
        #
        #
        #                 else:
        #                     temp_movie_genre = temp_movie_genre.split(' ')
        #                     temp_movie_genre = temp_movie_genre[0]
        #
        #                     temp_cold_movies = Movie.objects.filter(genre=temp_movie_genre, year__range=(
        #                     temp_movie_year[i] - 11, temp_movie_year[i] - 4)).exclude(Q(id=temp_movie_id[i]))
        #
        #                     if temp_cold_movies.count() >= 6:
        #                         temp_cold_movies = best_fetched
        #
        #
        #                     else:
        #                         normal_fetched = Movie.objects.filter(Q(genre=temp_movie_genre)).exclude(
        #                             Q(id=temp_movie_id[i]))
        #                         temp_cold_movies = normal_fetched
        #
        #
        #
        #             except:
        #
        #                 temp_movie_genre = temp_movie_genre[0]
        #                 best_fetched = Movie.objects.filter(genre=temp_movie_genre, year__range=(
        #                 temp_movie_year[i] - 11, temp_movie_year[i] - 4)).exclude(Q(id=temp_movie_id[i]))
        #
        #                 if best_fetched.count() >= 6:
        #                     temp_cold_movies = best_fetched
        #
        #                 else:
        #                     normal_fetched = Movie.objects.filter(Q(genre=temp_movie_genre)).exclude(
        #                         Q(id=temp_movie_id[i]))
        #                     temp_cold_movies = normal_fetched
        #
        #         for j in range(0, len(temp_cold_movies)):
        #             cold_recommended_movies.append(temp_cold_movies[j].title)

        # Two differen list lai merge garera unique banayeko .... Note: Numpy bata garda chai hamiley unique ta hunthyo tara order bigrincha.



        merged_recommended_movies = all_recommended_movies + cold_recommended_movies

        unique_merged_movies = []

        for x in merged_recommended_movies:
            if x not in unique_merged_movies:
                unique_merged_movies.append(x)

        # all_recommend = unique_merged_movies



        i = 0
        for movie in unique_merged_movies:
            if not check_seen(movie, name):
                movielist.append(movie)

            i = i + 1
            if i >= 100 + length:
                break

        return movielist

    except:
        return movielist
