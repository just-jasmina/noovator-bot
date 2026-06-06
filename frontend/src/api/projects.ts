import { apiClient } from './client'
import type { Project, Comment } from '../types'

export const projectsApi = {
  list: async (params?: { tag?: string; sort?: string; page?: number }) => {
    const res = await apiClient.get<Project[]>('/projects', { params })
    return res.data
  },

  get: async (id: number): Promise<Project> => {
    const res = await apiClient.get<Project>(`/projects/${id}`)
    return res.data
  },

  myProjects: async (): Promise<Project[]> => {
    const res = await apiClient.get<Project[]>('/projects/my')
    return res.data
  },

  create: async (data: Record<string, unknown>): Promise<Project> => {
    const res = await apiClient.post<Project>('/projects', data)
    return res.data
  },

  update: async (id: number, data: Record<string, unknown>): Promise<Project> => {
    const res = await apiClient.put<Project>(`/projects/${id}`, data)
    return res.data
  },

  uploadDocument: async (id: number, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    const res = await apiClient.post(`/projects/${id}/documents`, fd)
    return res.data
  },

  getComments: async (projectId: number): Promise<Comment[]> => {
    const res = await apiClient.get<Comment[]>(`/comments/project/${projectId}`)
    return res.data
  },

  addComment: async (projectId: number, content: string, parentId?: number) => {
    const res = await apiClient.post(`/comments/project/${projectId}`, { content, parent_id: parentId })
    return res.data
  },
}
