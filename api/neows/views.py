from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from django.urls import reverse
import requests

from datetime import datetime, timedelta

API_KEY = 'qgYuUvBQlFNH8tI9GiqqbsExq5vSTjGxBj3iNYxN'

class AsteroidAPIView(APIView):

    date_format = "%Y-%m-%d"
    start_date_obj = None
    end_date_obj = None

    def retrieve_data(self):

        start_date = self.start_date_obj.strftime(self.date_format)
        end_date = None
        if self.end_date_obj - self.start_date_obj > timedelta(days=7):
            end_date = (self.start_date_obj+timedelta(days=7)).strftime(self.date_format)
        else:
            end_date = self.end_date_obj.strftime(self.date_format)

        url = f'https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={API_KEY}'
        response = requests.get(url).json()

        return response

    def filter_data(self, data):

        neows = data["near_earth_objects"]
        filtered = {}

        for date_key in neows.keys():
            content_at_date = neows[date_key]
            objs_at_date = []
            for obj in content_at_date:
                obj_data = {}
                obj_data["date"] = obj["close_approach_data"][0]["close_approach_date_full"]
                obj_data["name"] = obj["name"]
                obj_data["distance"] = obj["close_approach_data"][0]["miss_distance"]
                obj_data["estimated_diameter"] = obj["estimated_diameter"]

                objs_at_date.append(obj_data)

            filtered[date_key] = objs_at_date

        return filtered

    def sort_data(self, data):

        sorted_data = [(key, sorted(data[key], key=lambda item: item["date"])) for key in data.keys()]

        return sorted(sorted_data, key=lambda tup: tup[0])

    def get(self, *args, **kwargs):

        try:
            query_params = self.request.query_params
            start_date = query_params.get('start_date')
            end_date = query_params.get('end_date')

            self.start_date_obj, self.end_date_obj = sorted([datetime.strptime(start_date, self.date_format),
                                                    datetime.strptime(end_date, self.date_format)])

        except (TypeError, ValueError):
            raise ParseError(f"Must specify both 'start_date' and 'end_date' parameters - format {reverse('main-request')}?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD")

        else:

            data = self.retrieve_data()
            filtered_data = self.filter_data(data)
            sorted_data = self.sort_data(filtered_data)

            return Response(sorted_data)