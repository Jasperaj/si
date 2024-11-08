import streamlit as st
from todoist_api_python.api import TodoistAPI

# Function to list all projects with their IDs and tasks
def list_projects_and_tasks(api):
    try:
        projects = api.get_projects()
        if not projects:
            return "No projects found."

        project_details = []
        for project in projects:
            tasks = api.get_tasks(project_id=project.id)
            task_list = "\n".join([f"  - {task.content}" for task in tasks]) if tasks else "  No tasks."
            project_info = f"**{project.name}** (ID: {project.id})\n{task_list}"
            project_details.append(project_info)

        return "\n\n".join(project_details)
    except Exception as e:
        return f"An error occurred: {e}"

# Main function for the Streamlit app
def project_task_viewer():
    st.title("Todoist Project and Task Viewer")

    # Input field for the API key (ensure to handle this securely in production)
    api_key = '81f5c6bfb82cbc099dd980ac5e545a868881dafb'

    if api_key:
        # Initialize the Todoist API with the provided key
        api = TodoistAPI(api_key)

        if st.button("Get Projects and Tasks"):
            project_data = list_projects_and_tasks(api)
            st.markdown(project_data)
    else:
        st.warning("Please enter your Todoist API Key.")

# Run the app
if __name__ == "__main__":
    project_task_viewer()
