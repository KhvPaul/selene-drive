# Service Workpiece

### Local setup

* Run `docker-compose build` or  `docker-compose build --no-cache` to build
* Then `docker-compose up` to run server


### Branch and commit naming convention

Follow gitflow's branch model:

* `feature/NAME` - for any tasks, improvements
* `bugfix/NAME` - for bugs 

NAME should follow these rules:

* NAME should start with task ID, eg. `feature/CR-2024`
* add a short description to name with lowercase and using hyphen between words: e.g `feature/CR-2024-add-pg-bouncer`

All commit's comments should start with task ID and then a short description. For example:

* `CR-2895 - fixed bug related to ...`
* `CR-2859 - code refactoring based on feedback from PR`


### Pull request merge flow

Each developer to merge his own pull requests. Necessary condition:

* 1+ approvals 

Merge tips (always run before merge):

* `git checkout "source-branch"` (eg. `feature/CR-1238` is the source branch, `develop` is the target branch)
* `git pull origin dev`
* fix conflicts
* fix alembic migrations
* `tox`
* `git commit`
* `git push`
* merge (click the ‘Merge’ button on Bitbucket, after getting approve)


### Admin panel

Amis admin is being used for admin panel. You can reach it by http://localhost:8000/admin/
