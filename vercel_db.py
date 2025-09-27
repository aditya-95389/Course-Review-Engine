"""
Vercel-compatible database module using environment variables and in-memory storage
Since Vercel functions are stateless, we'll use a combination of:
1. Environment variables for simple data
2. External storage APIs (could be added later)
3. In-memory data structures initialized on startup
"""

import json
import os
import hashlib
from typing import Dict, List, Optional, Any

class VercelDB:
    def __init__(self):
        # Initialize in-memory storage
        self.users = {}
        self.courses = {}
        self.reviews = {}
        self.reset_tokens = {}
        self._init_sample_data()
    
    def _init_sample_data(self):
        """Initialize with sample course data"""
        self.courses = {
            1: {
                'id': 1,
                'name': 'Python Programming',
                'provider': 'Coursera',
                'desc': 'Complete Python course from basics to advanced',
                'url': 'https://coursera.org/python'
            },
            2: {
                'id': 2,
                'name': 'React Development',
                'provider': 'Udemy',
                'desc': 'Build modern web apps with React and hooks',
                'url': 'https://udemy.com/react'
            },
            3: {
                'id': 3,
                'name': 'Machine Learning',
                'provider': 'Stanford',
                'desc': 'Andrew Ng ML course with practical projects',
                'url': 'https://coursera.org/ml'
            },
            4: {
                'id': 4,
                'name': 'Digital Marketing',
                'provider': 'Google',
                'desc': 'Complete digital marketing and SEO course',
                'url': 'https://skillshop.withgoogle.com'
            },
            5: {
                'id': 5,
                'name': 'UI/UX Design',
                'provider': 'Adobe',
                'desc': 'Design thinking and user experience principles',
                'url': 'https://adobe.com/education'
            }
        }
        
        # Add a default user for testing
        default_email = 'adityaroyal5398@gmail.com'
        default_password = '5cbb50c74a33bdba19336457d6cd4a27e292d59309f456f3eaeffb98e24fdd3e'  # hashed password
        self.users[default_email] = {
            'id': 1,
            'email': default_email,
            'password': default_password
        }
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        return self.users.get(email)
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        for user in self.users.values():
            if user['id'] == user_id:
                return user
        return None
    
    def create_user(self, email: str, password_hash: str) -> Dict:
        """Create a new user"""
        if email in self.users:
            raise ValueError("Email already exists")
        
        # Generate new user ID
        new_id = max([user['id'] for user in self.users.values()], default=0) + 1
        
        user = {
            'id': new_id,
            'email': email,
            'password': password_hash
        }
        
        self.users[email] = user
        return user
    
    def get_all_courses(self) -> List[Dict]:
        """Get all courses with review stats"""
        courses_with_stats = []
        
        for course in self.courses.values():
            course_reviews = [r for r in self.reviews.values() if r['course_id'] == course['id']]
            
            if course_reviews:
                avg_rating = sum(r['rating'] for r in course_reviews) / len(course_reviews)
                review_count = len(course_reviews)
            else:
                avg_rating = None
                review_count = 0
            
            course_data = course.copy()
            course_data['avg'] = avg_rating
            course_data['cnt'] = review_count
            courses_with_stats.append(course_data)
        
        return courses_with_stats
    
    def search_courses(self, search_term: str) -> List[Dict]:
        """Search courses by name or provider"""
        search_term = search_term.lower()
        matching_courses = []
        
        for course in self.courses.values():
            if (search_term in course['name'].lower() or 
                search_term in course['provider'].lower()):
                
                course_reviews = [r for r in self.reviews.values() if r['course_id'] == course['id']]
                
                if course_reviews:
                    avg_rating = sum(r['rating'] for r in course_reviews) / len(course_reviews)
                    review_count = len(course_reviews)
                else:
                    avg_rating = None
                    review_count = 0
                
                course_data = course.copy()
                course_data['avg'] = avg_rating
                course_data['cnt'] = review_count
                matching_courses.append(course_data)
        
        return matching_courses
    
    def get_course_by_id(self, course_id: int) -> Optional[Dict]:
        """Get course by ID"""
        return self.courses.get(course_id)
    
    def get_course_reviews(self, course_id: int) -> List[Dict]:
        """Get all reviews for a course"""
        course_reviews = []
        
        for review in self.reviews.values():
            if review['course_id'] == course_id:
                # Add user email to review
                user = self.get_user_by_id(review['user_id'])
                if user:
                    review_with_user = review.copy()
                    review_with_user['email'] = user['email']
                    course_reviews.append(review_with_user)
        
        return course_reviews
    
    def create_review(self, user_id: int, course_id: int, rating: int, text: str) -> Dict:
        """Create a new review"""
        # Generate new review ID
        new_id = max([r['id'] for r in self.reviews.values()], default=0) + 1
        
        review = {
            'id': new_id,
            'user_id': user_id,
            'course_id': course_id,
            'rating': rating,
            'text': text
        }
        
        self.reviews[new_id] = review
        return review
    
    def update_review(self, review_id: int, rating: int, text: str, user_id: int) -> bool:
        """Update a review (only by the owner)"""
        review = self.reviews.get(review_id)
        if review and review['user_id'] == user_id:
            review['rating'] = rating
            review['text'] = text
            return True
        return False
    
    def delete_review(self, review_id: int, user_id: int) -> bool:
        """Delete a review (only by the owner)"""
        review = self.reviews.get(review_id)
        if review and review['user_id'] == user_id:
            del self.reviews[review_id]
            return True
        return False
    
    def store_reset_token(self, email: str, token: str, expires: int):
        """Store password reset token"""
        self.reset_tokens[token] = {
            'email': email,
            'expires': expires
        }
    
    def get_reset_token(self, token: str) -> Optional[Dict]:
        """Get reset token data"""
        return self.reset_tokens.get(token)
    
    def delete_reset_token(self, token: str):
        """Delete reset token"""
        if token in self.reset_tokens:
            del self.reset_tokens[token]
    
    def update_user_password(self, email: str, password_hash: str) -> bool:
        """Update user password"""
        if email in self.users:
            self.users[email]['password'] = password_hash
            return True
        return False

# Global database instance
_db_instance = None

def get_db():
    """Get global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = VercelDB()
    return _db_instance
