import django_filters		#import garna parxa
from django_filters import DateFilter, CharFilter, NumberFilter, ChoiceFilter  	# django_filters batw pani ajjai DateFilter and CharFilter lai import gareko

from .models import *

class MovieFilter(django_filters.FilterSet):
	# imdbrating = django_filters.CharFilter(lookup_expr='gte')

	IMDBRATING = (				#Choices or dropdown choices 
			(1, ' 1 + '),
			(2, ' 2 + '),
			(3, ' 3 + '),
			(4, ' 4 + '),
			(5, ' 5 + '),
			(6, ' 6 + '),
			(7, ' 7 + '),
			(8, ' 8 + '),
			(9, ' 9 + ')
			)

	imdbrating = django_filters.ChoiceFilter(label='imdbrating', choices=IMDBRATING, lookup_expr='gte')

	class Meta:
		model = Movie
		# fields = '__all__'

		fields = ['genre','year']


		# fields = ['genre',
		# 			 'year',
		# 			  'imdbrating']

		# fields = {
        #     'genre': ['exact', ],
        #     'year': ['exact', ],
        #     'imdbrating': ['gte', ],
        # }


		exclude = ['title','poster']