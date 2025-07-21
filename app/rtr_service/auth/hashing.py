from passlib.context import CryptContext
pwd_cxt = CryptContext(schemes =["bcrypt"],deprecated="auto")
class Hash():
   def bcrypt(password:str): #This method hashes the provided password using the bcrypt algorithm through the CryptContext object (pwd_cxt) and returns the hashed password.
      return pwd_cxt.hash(password)
   def verify(hashed,normal): #This method verifies whether the plain text password matches the hashed password.
      return pwd_cxt.verify(normal,hashed)