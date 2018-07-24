# Mini Unsplash



In this project:

   Mini Unsplash is built to help users identify their preferences for photography and search for the picture that matches their preference all in one application.

  * Search for copyright free, high quality images from Unsplash
  * Search result shows:
      * Number of likes
      * Photo
      * Download link
      * Color picked out by the photo
  * Register and Sign in to
      * Make unique collections from the photos by choosing the number of likes
      * Submit a form about their background/wallpaper preferences and update and delete their forms
  * The application saves: each user, each photo searched, each collection, and each preference form
  * Allows each logged-in user to see all of the collections they have made as well as their preference forms
  * One logged in user cannot see another logged in user's collections or forms

## Requirements
### Installations:

  * `flask` library and all `flask`-related modules we have used in SI364
  * There are no additional modules you should install.

### Other

  * You must have a file called `unspalsh_client_id.py` in the same directory as the `app.py` file, of the same format as the one included, but with API key filled in. You can get an API key at https://unsplash.com/developers.
  * NOTE: A sample file with API keys is included in a file on Canvas for SI 364, so as not to include it on GitHub. (Of course, this repository is private, but just in case I decide to change that, I am not committing any API keys to GitHub!)


## What to do to run this application

  * `cd` to the directory in which the app files live
  * run, in Python `python app.py runserver`
  * You should see a home page prompting you to log in or register
  * Log in (register if you don't have an account, and then log in)
  * You should see a search bar to search photos from Unsplash, type in any keyword you would like to search for photos
      * For example, type `water` into the first box
      * You should be redirected to a page that renders photos, and can use the navigation to see other pages!
  * Here are the suggested terms you should enter for each form:


## Routes in this application

  * `/` -> `base.html`
  * `/photo_searched` -> `searched_photos.html`
  * `/search_terms` -> `search_terms.html`
  * `/all_photos` -> `all_photos.html`
  * `/create_collection` -> `create_collection.html` (login restricted)
  * `/collections` -> `collections.html` (login restricted)
  * `/collection/<id_num>` -> `collection.html` (login restricted)
  * `/background` -> `create_background.html` (login restricted)
  * `/b_info` -> `backgrounds.html` (login restricted)
  * `/one_bg/<ident>` -> `background.html` (login restricted)
  * `/update/<pref>` -> `update_info.html` (login restricted)




 

