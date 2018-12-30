from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from twitter_app.models import Tweet
from .pagination import StandardResultPagination
from .serializers import TweetModelSerializer
from django.db.models import Q


class RetweetApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, format=None):
        tweet_qs = Tweet.objects.filter(pk=pk)
        message = 'Not allowed'
        if tweet_qs.exists() and tweet_qs.count() == 1:
            # if request.user.is_authenticated:
            new_tweet = Tweet.objects.retweet(request.user, tweet_qs.first())
            if new_tweet is not None:
                data = TweetModelSerializer(new_tweet).data
                return Response(data)
            message = "Cannot retweet the same in 1 day"
        return Response({'message': message}, status=400)


class TweetCreateAPIView(generics.CreateAPIView):
    serializer_class = TweetModelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TweetListAPIView(generics.ListAPIView):
    serializer_class = TweetModelSerializer
    pagination_class = StandardResultPagination

    def get_queryset(self, *args, **kwargs):
        requested_user = self.kwargs.get('username')
        if requested_user:
            qs = Tweet.objects.filter(user__username=requested_user).order_by('-timestamp')
        else:
            im_following = self.request.user.profile.get_following()
            qs1 = Tweet.objects.filter(user__in=im_following)
            qs2 = Tweet.objects.filter(user=self.request.user)
            qs = (qs1 | qs2).distinct().order_by('-timestamp')

        query = self.request.GET.get('q', None)
        if query is not None:
            qs = qs.filter(
                Q(content__icontains=query) |
                Q(user__username__icontains=query)
            )
        return qs
