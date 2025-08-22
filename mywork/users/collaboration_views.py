from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, CollaborationRequest

class SendCollaborationRequestView(APIView):
    def post(self, request):
        try:
            data = request.data
            investor_id = data.get('investor_id')
            entrepreneur_id = data.get('entrepreneur_id')
            message = data.get('message', '')
            
            # Get users
            investor = User.objects.get(id=investor_id)
            entrepreneur = User.objects.get(id=entrepreneur_id)
            
            # Create collaboration request
            collaboration_request = CollaborationRequest.objects.create(
                investor=investor,
                entrepreneur=entrepreneur,
                message=message,
                status='Pending'
            )
            
            return Response({
                'success': True,
                'message': 'Collaboration request sent successfully',
                'request_id': collaboration_request.id
            })
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CollaborationRequestListView(APIView):
    def get(self, request):
        user_id = request.GET.get('user_id')
        user_role = request.GET.get('role')
        
        try:
            if user_role == 'entrepreneur':
                # Get requests received by entrepreneur
                requests = CollaborationRequest.objects.filter(entrepreneur_id=user_id)
                request_data = []
                
                for req in requests:
                    request_data.append({
                        'id': req.id,
                        'investor_name': req.investor.username,
                        'investor_email': req.investor.email,
                        'message': req.message,
                        'status': req.status,
                        'created_at': req.created_at.strftime('%Y-%m-%d %H:%M'),
                    })
                    
            elif user_role == 'investor':
                # Get requests sent by investor
                requests = CollaborationRequest.objects.filter(investor_id=user_id)
                request_data = []
                
                for req in requests:
                    request_data.append({
                        'id': req.id,
                        'entrepreneur_name': req.entrepreneur.username,
                        'entrepreneur_email': req.entrepreneur.email,
                        'message': req.message,
                        'status': req.status,
                        'created_at': req.created_at.strftime('%Y-%m-%d %H:%M'),
                    })
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid role'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            return Response({
                'success': True,
                'requests': request_data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateCollaborationRequestView(APIView):
    def patch(self, request, request_id):
        try:
            collaboration_request = CollaborationRequest.objects.get(id=request_id)
            new_status = request.data.get('status')
            
            if new_status in ['Accepted', 'Rejected']:
                collaboration_request.status = new_status
                collaboration_request.save()
                
                return Response({
                    'success': True,
                    'message': f'Request {new_status.lower()} successfully'
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid status'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except CollaborationRequest.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Request not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
