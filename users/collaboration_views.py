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
            initiated_by = data.get('initiated_by') if data.get('initiated_by') in ('investor', 'entrepreneur') else 'investor'
            # If current authenticated user exists and has role, infer initiator
            user = getattr(request, 'user', None)
            try:
                if not data.get('initiated_by') and user and getattr(user, 'is_authenticated', False) and getattr(user, 'role', None) in ('investor', 'entrepreneur'):
                    initiated_by = user.role
                elif not data.get('initiated_by'):
                    # Fallback: if investor_id matches an investor user, set accordingly
                    if investor_id and User.objects.filter(id=investor_id, role='investor').exists():
                        initiated_by = 'investor'
                    elif entrepreneur_id and User.objects.filter(id=entrepreneur_id, role='entrepreneur').exists():
                        initiated_by = 'entrepreneur'
            except Exception:
                pass
            
            # Get users
            investor = User.objects.get(id=investor_id)
            entrepreneur = User.objects.get(id=entrepreneur_id)
            
            # Create collaboration request
            collaboration_request = CollaborationRequest.objects.create(
                investor=investor,
                entrepreneur=entrepreneur,
                message=message,
                status='Pending',
                initiated_by=initiated_by
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
        # if 'true', only requests initiated by the other side
        inbox = request.GET.get('inbox')

        try:
            if user_role == 'entrepreneur':
                # Get requests received by entrepreneur
                qs = CollaborationRequest.objects.filter(entrepreneur_id=user_id)
                if inbox == 'true':
                    qs = qs.filter(initiated_by='investor')
                requests = qs
                request_data = []
                
                for req in requests:
                    request_data.append({
                        'id': req.id,
                        'investor_name': req.investor.username,
                        'investor_email': req.investor.email,
                        'message': req.message,
                        'status': req.status,
                        'initiated_by': req.initiated_by,
                        'created_at': req.created_at.strftime('%Y-%m-%d %H:%M'),
                    })
                    
            elif user_role == 'investor':
                # Get requests sent by investor
                qs = CollaborationRequest.objects.filter(investor_id=user_id)
                # For investor inbox: requests initiated by entrepreneur (pitches)
                if inbox == 'true':
                    qs = qs.filter(initiated_by='entrepreneur')
                requests = qs
                request_data = []
                
                for req in requests:
                    request_data.append({
                        'id': req.id,
                        'entrepreneur_name': req.entrepreneur.username,
                        'entrepreneur_email': req.entrepreneur.email,
                        'message': req.message,
                        'status': req.status,
                        'initiated_by': req.initiated_by,
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
                # Only allow the recipient side (the opposite of initiator) to change status
                user = getattr(request, 'user', None)
                if not user or not getattr(user, 'is_authenticated', False):
                    return Response({'success': False, 'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
                # Determine who is allowed
                allowed = False
                if collaboration_request.initiated_by == 'investor' and user.id == collaboration_request.entrepreneur_id:
                    allowed = True
                if collaboration_request.initiated_by == 'entrepreneur' and user.id == collaboration_request.investor_id:
                    allowed = True
                if not allowed:
                    return Response({'success': False, 'error': 'Not allowed to update this request'}, status=status.HTTP_403_FORBIDDEN)
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
