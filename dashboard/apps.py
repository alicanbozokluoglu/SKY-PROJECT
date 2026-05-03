from django.apps import AppConfig
# this imports a special Django class used to configure an app


class DashboardConfig(AppConfig):
    # this class tells Django about your app

    name = 'dashboard'
    # this is the name of your app
    # Django uses this to find the app and connect everything together


#This file tells Django “there is an app called dashboard