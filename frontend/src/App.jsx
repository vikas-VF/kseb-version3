
import { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import MainContent from "./components/MainContent";
import TopBar from "./components/TopBar";
import WorkflowStepper from "./components/WorkflowStepper";
import { ProcessProvider } from "./components/ProcessContext";
import { NotificationProvider } from "./contexts/NotificationContext";
import ErrorBoundary from "./components/ErrorBoundary";
import { Toaster, toast } from 'react-hot-toast';
import axios from 'axios';

// Configure global axios error handler
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 404) {
      console.error('API endpoint not found:', error.config?.url);
    } else if (error.response?.status === 500) {
      toast.error('Server error. Please check backend logs.');
    } else if (error.code === 'ERR_NETWORK') {
      toast.error('Network error. Please check your connection.');
    } else if (error.message === 'canceled') {
      // Ignore canceled requests
    }
    return Promise.reject(error);
  }
);

function App() {
    const [selected, setSelected] = useState(() => sessionStorage.getItem('selectedPage') ? JSON.parse(sessionStorage.getItem('selectedPage')) : "Home");
    const [activeProject, setActiveProject] = useState(() => sessionStorage.getItem('activeProject') ? JSON.parse(sessionStorage.getItem('activeProject')) : null);
    const [collapsed, setCollapsed] = useState(() => localStorage.getItem("sidebarCollapsed") !== null ? JSON.parse(localStorage.getItem("sidebarCollapsed")) : false);
    const [createProjectRenderKey, setCreateProjectRenderKey] = useState(0);
    const [loadProjectRenderKey, setLoadProjectRenderKey] = useState(0);

    useEffect(() => {
        const validateAndSetProject = async () => {
            if (activeProject?.path) {
                try {
                    const response = await axios.get('/project/check-directory', { params: { path: activeProject.path } });
                    if (!response.data.isValid) {
                        sessionStorage.removeItem('activeProject');
                        sessionStorage.removeItem('selectedPage');
                        setActiveProject(null);
                        setSelected("Home");
                    }
                } catch (error) {
                    sessionStorage.removeItem('activeProject');
                    sessionStorage.removeItem('selectedPage');
                    setActiveProject(null);
                    setSelected("Home");
                }
            }
        };
        validateAndSetProject();
    }, []);

    useEffect(() => {
        if (activeProject) {
            sessionStorage.setItem('activeProject', JSON.stringify(activeProject));
        } else {
            sessionStorage.removeItem('activeProject');
        }
    }, [activeProject]);

    useEffect(() => {
        sessionStorage.setItem('selectedPage', JSON.stringify(selected));
    }, [selected]);

    useEffect(() => {
        localStorage.setItem("sidebarCollapsed", JSON.stringify(collapsed));
    }, [collapsed]);
    
    const navigateTo = (page) => {
        if (page === 'Create Project') setCreateProjectRenderKey(prev => prev + 1);
        if (page === 'Load Project') setLoadProjectRenderKey(prev => prev + 1);
        setSelected(page);
    };

    return (
        <ErrorBoundary navigateTo={navigateTo}>
            <NotificationProvider>
                <ProcessProvider navigateTo={navigateTo}>
                    <div className="relative min-h-screen bg-slate-50 font-sans">
                        <Toaster position="top-center" />

                        <TopBar activeProject={activeProject} />

                        {/* Main container for content below the TopBar */}
                        <div className="pt-16">
                            {/* Column 1: Left Sidebar (Fixed) */}
                            <div className="fixed top-16 left-0 h-[calc(100vh-4rem)] z-30">
                                <Sidebar
                                    selected={selected}
                                    setSelected={navigateTo}
                                    collapsed={collapsed}
                                    setCollapsed={setCollapsed}
                                />
                            </div>

                            {/* Column 2: Main Content Area */}
                            {/* ✅ Margins now correctly account for both sidebars */}
                            <div
                                className={`transition-all duration-300 ease-in-out ${collapsed ? 'ml-20' : 'ml-72'} mr-20`}
                            >
                                <MainContent
                                    selected={selected}
                                    setSelected={navigateTo}
                                    activeProject={activeProject}
                                    setActiveProject={setActiveProject}
                                    createProjectRenderKey={createProjectRenderKey}
                                    loadProjectRenderKey={loadProjectRenderKey}
                                />
                            </div>

                            {/* Column 3: Right Workflow Stepper (Fixed) */}
                            <div className="fixed top-16 right-0 h-[calc(100vh-4rem)] w-20 z-20">
                                <WorkflowStepper
                                    selected={selected}
                                    setSelected={navigateTo}
                                    activeProject={activeProject}
                                />
                            </div>
                        </div>
                    </div>
                </ProcessProvider>
            </NotificationProvider>
        </ErrorBoundary>
    );
}

export default App;