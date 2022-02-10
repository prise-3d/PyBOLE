Installation
============


Install requirements
~~~~~~~~~~~~~~~~~~~~

With your python version (ideally python >= 3.7), you can the following required modules:

.. code:: bash
   
   pip install -r requirements.txt


Initialize the database with the following command:

.. code:: bash

   python manage.py makemigrations
   python manage.py migrate


Configure server
~~~~~~~~~~~~~~~~

Add your own super user admin credentials:

.. code:: bash

   cp credentials.example.json credentials.json
   


.. code-block:: json

   {
      "username":"username",
      "email":"",
      "password":"pass"
      "secret_key": "******"
   }

You can generate and replace the secret key param:

.. code:: python

   import uuid
   str(uuid.uuid4())


.. caution:: 

   Django requires a secret key to securing signed data.


Run the web application
~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   python manage.py runserver 8080

.. note::
   the administrator interface is now available: ``http://127.0.0.1:8080/admin``

Using docker
~~~~~~~~~~~~~~~~

First, you need to add your own user admin credentials wished:

.. code:: bash

   cp credentials.example.json credentials.json


Then, use make commands:

.. code:: bash

   make build
   make run


Or simply:

.. code:: bash

   make deploy


You also have ``stop``, ``remove``, ``clean`` commands:
- ``stop``: stop current container instance if exists
- ``remove``: stop and remove container instance if exists
- ``clean``: remove docker image if exists



