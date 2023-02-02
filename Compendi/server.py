import os
from flask import (
  Flask,
  render_template,
  request, 
  flash, 
  session, 
  redirect, 
  url_for
  )
from flask_login import (
  LoginManager, 
  login_required, 
  login_user, 
  logout_user,
  current_user,
  set_login_view
  )
from cloudinary.utils import cloudinary_url
from cloudinary.uploader import upload
import cloudinary
from model import (
  connect_to_db, 
  db, 
  Users, 
  Projects, 
  Folders, 
  Files, 
  Sections, 
  Images
  )
from crud import (
  get_file_by_id,
  get_image_by_id,
  get_folder_by_id,
  get_project_by_id,
  get_section_by_id,
  get_user_by_id,
  get_user_by_username,
  get_user_projects,
  get_sections,
  get_images
  )
from forms import (
  LoginForm, 
  RegisterForm, 
  ProjectCreationForm,
  FolderFileCreationForm,
  FileMainForm,
  FileImageForm,
  FileSectionForm
  )

# App & Secret Key config
app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

# Login Manager config
login_manager = LoginManager()
login_manager.init_app(app)
set_login_view = 'login'
LoginManager.login_message = 'Please login first.'


#  Cloudinary Config
cloudinary.config(
  cloud_name = os.environ['CLOUDNAME'],
  api_key = os.environ['CLOUDAPIKEY'],
  api_secret = os.environ['APISECRET'],
  secure = True
)

# Upload
# upload("https://upload.wikimedia.org/wikipedia/commons/a/ae/Olympic_flag.jpg", public_id="olympic_flag")

# Transform
# url, options = cloudinary_url("olympic_flag", width=100, height=150, crop="fill")


############ LOGIN MANAGEMENT ############

@login_manager.user_loader
def load_user(user_id):
  return get_user_by_id(user_id)

@app.route('/login', methods=['POST', 'GET'])
def login():
  login_form = LoginForm()
  
  if login_form.validate_on_submit():
    user = get_user_by_username(login_form.username.data)
    print(user)
    
    if user:
      if user.check_password(login_form.password.data):
        user.authenticated = True
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=login_form.remember.data)
        flash('Logged in successfully.', 'message')
        
        return redirect(url_for("projects"))
    flash('Input invalid, please try again.', 'error')
      
  return render_template('login.html', login_form=login_form)

@app.route('/register', methods=['POST', 'GET'])
def register():
  form = RegisterForm()
  
  if form.validate_on_submit():
    if Users.query.filter_by(username=form.username.data).first() == None:
      if Users.query.filter_by(email=form.email.data).first() == None:
        new_user = Users(form.email.data, form.username.data, form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash("You've been registered! Please log in.", 'message')
        return redirect(url_for('login'))
      else: flash('Email already in use.', 'error')
    else: flash('Username already in use.', 'error') 
    
  return render_template('register.html', form=form)

@app.route('/logout', methods=['GET'])
@login_required
def logout():
  logout_user()
  flash('Logged out successfully.', 'message')
  return redirect(url_for('login'))


############ VIEW FUNCTIONS ############

@app.route('/')
def homepage():
  return render_template('homepage.html',)

@app.route('/projects', methods=['POST', 'GET'])
@login_required
def projects():
  add_project_form = ProjectCreationForm()
  
  if add_project_form.validate_on_submit():
    current_user.add_project(name=add_project_form.project_name.data, desc=add_project_form.desc.data)
  
  return render_template('projects.html', projects=get_user_projects(current_user.id), add_project_form=add_project_form)

@app.route('/add-project')
@login_required
def add_project():
  return "add a project"

@app.route('/folder-view/<folder_id>', methods=['POST', 'GET'])
@login_required
def folder_view(folder_id):
  child_creation_form = FolderFileCreationForm()
  
  open_folder = get_folder_by_id(folder_id)
  project = get_project_by_id(open_folder.project_id)
  children = open_folder.get_children()
  
  if child_creation_form.validate_on_submit():
    if child_creation_form.type_selection.data == 'folder':
      open_folder.add_folder(name=child_creation_form.name.data)
    else:
      open_folder.add_file(name=child_creation_form.name.data, sub_name="")
    
  return render_template('folder_view.html', folder=open_folder, project=project, children=children, create_form=child_creation_form)

@app.route('/file-view/<file_id>', methods=['POST', 'GET'])
@login_required
def file_view(file_id):
  open_file = get_file_by_id(file_id)
  main_form = FileMainForm()
  image_form = FileImageForm()
  section_form = FileSectionForm()
  
  return render_template(
    'file_view.html', 
    open_file=open_file, 
    main_form=main_form, 
    image_form=image_form, 
    section_form=section_form,
    sections=get_sections(file_id),
    images=get_images(file_id)
    )
  
@app.route('/file-edit/<file_id>', methods=['POST', 'GET'])
@login_required
def file_edit(file_id):
  open_file = get_file_by_id(file_id)
  sections = get_sections(file_id)
  images = get_images(file_id)
  main_form = FileMainForm()
  image_form = FileImageForm()
  section_form = FileSectionForm()
  
  return render_template(
    'file_edit.html', 
    open_file=open_file, 
    main_form=main_form, 
    image_form=image_form, 
    section_form=section_form,
    sections=get_sections(file_id),
    images=get_images(file_id)
    )

@app.route('/file-edit/add-section', methods=['POST', 'GET'])
@login_required
def add_section():
  name = request.get_datasectionBody
  print(name)
  return 'Hello'

# @app.route('/projects/<project_id>/<parent_folder_id>')
# @login_required
# def file_view(project_id, parent_folder_id, file_id):
#   open_file = get_file_by_id(file_id)
#   parent_folder = get_folder_by_id(parent_folder_id)
#   project = get_project_by_id(project_id)
  
#   return render_template('file.html', file=open_file, parent_folder_name=parent_folder.name, project_name=project.name )

@app.route('/projects/<project_id>/add-child')
@login_required
def add_child(project_id):
  return "add a child"

@app.route('/projects/<project_id>/settings')
@login_required
def child_settings(project_id, folder):
  return f"{folder.folder_id}folder settings"


if __name__ == "__main__":
  connect_to_db(app)
  app.run(debug=True)