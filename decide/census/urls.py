from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.CensusCreate.as_view(), name='census_create'),
    path('<int:voting_id>/', views.CensusDetail.as_view(), name='census_detail'),
    path('web/', views.listaCensos, name='list_census'),
    path('web/<int:voting_id>/', views.listaVotantes, name='list_cesus_by_voting'),
    path('web/export_csv', views.export_csv, name='exportar'),
    path('web/export_xlsx', views.export_excel, name='exportar1_excel'),
    path('web/add/<int:votingID>', views.addCensus, name='add_census'),
    path('web/add/', views.addCensus, name='add_census'),
    path('web/export_pdf', views.exportToPdf, name='exportar_pdf'),
    path('web/delete/<int:census_id>/', views.eliminaCenso, name='eliminaCenso'),
]