from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User

class UserListView(APIView):
    def get(self, request):
        users = User.objects.all()
        user_data = []
        
        for user in users:
            role = getattr(user, 'role', 'unknown')
            
            user_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': role,
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M'),
                'is_active': user.is_active
            })
        
        return Response({
            'success': True,
            'users': user_data,
            'total_count': len(user_data)
        })

class UserDeleteView(APIView):
    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            username = user.username
            user.delete()
            
            return Response({
                'success': True,
                'message': f'User {username} deleted successfully'
            })
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error deleting user: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserStatsView(APIView):
    def get(self, request):
        total_users = User.objects.count()
        investors = User.objects.filter(role='investor').count()
        entrepreneurs = User.objects.filter(role='entrepreneur').count()
        
        return Response({
            'success': True,
            'stats': {
                'total_users': total_users,
                'investors': investors,
                'entrepreneurs': entrepreneurs,
                'unknown_role': total_users - investors - entrepreneurs
            }
        })

class EntrepreneursListView(APIView):
    def get(self, request):
        entrepreneurs = User.objects.filter(role='entrepreneur')
        entrepreneur_data = []
        
        for user in entrepreneurs:
            entrepreneur_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined.strftime('%Y-%m-%d')
            })
        
        return Response({
            'success': True,
            'entrepreneurs': entrepreneur_data
        })

class InvestorsListView(APIView):
    def get(self, request):
        investors = User.objects.filter(role='investor')
        investor_data = []
        
        for user in investors:
            investor_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined.strftime('%Y-%m-%d')
            })
        
        return Response({
            'success': True,
            'investors': investor_data
        })
