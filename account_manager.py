import tweepy
import time
import random
from database import TwitterDatabase

class TwitterAccountManager:
    def __init__(self):
        self.db = TwitterDatabase()
        self.api_instances = {}

    def setup_api(self, account):
        """Hesap için Twitter API bağlantısını kurar"""
        auth = tweepy.OAuthHandler(account[4], account[5])  # api_key, api_secret
        auth.set_access_token(account[6], account[7])  # access_token, access_token_secret
        return tweepy.API(auth, wait_on_rate_limit=True)

    def get_api_for_account(self, account_id):
        """Hesap için API instance'ı döndürür, yoksa oluşturur"""
        if account_id not in self.api_instances:
            account = self.db.get_account_by_id(account_id)
            if account and all([account[4], account[5], account[6], account[7]]):
                self.api_instances[account_id] = self.setup_api(account)
            else:
                return None
        return self.api_instances[account_id]

    def follow_user(self, account_id, target_username):
        """Belirli bir kullanıcıyı takip eder"""
        try:
            api = self.get_api_for_account(account_id)
            if not api:
                return {"status": "error", "message": "API bağlantısı kurulamadı"}

            user = api.get_user(screen_name=target_username)
            api.create_friendship(user.id)
            
            # İşlemi logla
            self.db.log_action(
                account_id=account_id,
                action_type="follow",
                target_user=target_username
            )
            
            return {"status": "success", "message": f"{target_username} takip edildi"}
            
        except tweepy.TweepError as e:
            return {"status": "error", "message": str(e)}

    def like_tweet(self, account_id, tweet_id):
        """Belirli bir tweet'i beğenir"""
        try:
            api = self.get_api_for_account(account_id)
            if not api:
                return {"status": "error", "message": "API bağlantısı kurulamadı"}

            api.create_favorite(tweet_id)
            
            # İşlemi logla
            self.db.log_action(
                account_id=account_id,
                action_type="like",
                target_tweet_id=tweet_id
            )
            
            return {"status": "success", "message": f"Tweet beğenildi: {tweet_id}"}
            
        except tweepy.TweepError as e:
            return {"status": "error", "message": str(e)}

    def retweet(self, account_id, tweet_id):
        """Belirli bir tweet'i retweet eder"""
        try:
            api = self.get_api_for_account(account_id)
            if not api:
                return {"status": "error", "message": "API bağlantısı kurulamadı"}

            api.retweet(tweet_id)
            
            # İşlemi logla
            self.db.log_action(
                account_id=account_id,
                action_type="retweet",
                target_tweet_id=tweet_id
            )
            
            return {"status": "success", "message": f"Tweet retweet edildi: {tweet_id}"}
            
        except tweepy.TweepError as e:
            return {"status": "error", "message": str(e)}

    def bulk_follow(self, target_username, delay_range=(1, 5)):
        """Tüm aktif hesaplarla bir kullanıcıyı takip eder"""
        results = []
        active_accounts = self.db.get_active_accounts()
        
        for account in active_accounts:
            result = self.follow_user(account[0], target_username)
            results.append({
                "account": account[1],
                "result": result
            })
            
            # Rate limiting için rastgele bekleme
            time.sleep(random.uniform(*delay_range))
        
        return results

    def bulk_like(self, tweet_id, delay_range=(1, 5)):
        """Tüm aktif hesaplarla bir tweet'i beğenir"""
        results = []
        active_accounts = self.db.get_active_accounts()
        
        for account in active_accounts:
            result = self.like_tweet(account[0], tweet_id)
            results.append({
                "account": account[1],
                "result": result
            })
            
            # Rate limiting için rastgele bekleme
            time.sleep(random.uniform(*delay_range))
        
        return results

    def bulk_retweet(self, tweet_id, delay_range=(1, 5)):
        """Tüm aktif hesaplarla bir tweet'i retweet eder"""
        results = []
        active_accounts = self.db.get_active_accounts()
        
        for account in active_accounts:
            result = self.retweet(account[0], tweet_id)
            results.append({
                "account": account[1],
                "result": result
            })
            
            # Rate limiting için rastgele bekleme
            time.sleep(random.uniform(*delay_range))
        
        return results

def main():
    # Test için örnek kullanım
    manager = TwitterAccountManager()
    
    # Örnek: Tüm hesaplarla bir kullanıcıyı takip et
    results = manager.bulk_follow("example_user")
    print("Takip Sonuçları:", results)
    
    # Örnek: Tüm hesaplarla bir tweet'i beğen
    results = manager.bulk_like("1234567890")
    print("Beğeni Sonuçları:", results)

if __name__ == "__main__":
    main() 