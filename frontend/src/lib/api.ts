import { apiClient } from './apiClient';
import { 
  Version, 
  Material, 
  Section, 
  Topic, 
  Outline, 
  Lesson, 
  Slides,
  CurriculumDiff,
  OutlineItem,
  SuggestedOutline,
} from '@/types/api';

export const curriculumApi = {
  listVersions: async (): Promise<Version[]> => {
    const res = await apiClient.get('/curriculum/version/list');
    return res.data.versions;
  },

  createVersion: async (name: string, year: number, notes?: string): Promise<Version> => {
    const res = await apiClient.post('/curriculum/version', { name, year, notes });
    return res.data;
  },

  getVersion: async (id: number): Promise<Version> => {
    const res = await apiClient.get(`/curriculum/version/${id}`);
    return res.data;
  },

  deleteVersion: async (id: number): Promise<void> => {
    await apiClient.delete(`/curriculum/version/${id}`);
  },

  createOutline: async (curriculumVersionId: number, items: OutlineItem[]): Promise<Outline> => {
    const res = await apiClient.post('/curriculum/outline', {
      curriculum_version_id: curriculumVersionId,
      items,
    });
    return res.data;
  },

  listOutlines: async (curriculumVersionId: number): Promise<Outline[]> => {
    const res = await apiClient.get(`/curriculum/outline/list/${curriculumVersionId}`);
    return res.data.outlines;
  },

  getOutline: async (id: number): Promise<Outline> => {
    const res = await apiClient.get(`/curriculum/outline/${id}`);
    return res.data;
  },

  updateOutline: async (id: number, items: OutlineItem[]): Promise<Outline> => {
    const res = await apiClient.put(`/curriculum/outline/${id}`, { items });
    return res.data;
  },

  diffVersions: async (versionAId: number, versionBId: number): Promise<CurriculumDiff> => {
    const res = await apiClient.get(`/curriculum/diff/${versionAId}/${versionBId}`);
    return res.data;
  },

  suggestOutline: async (curriculumVersionId: number): Promise<SuggestedOutline> => {
    const res = await apiClient.post(`/curriculum/outline/suggest/${curriculumVersionId}`);
    return res.data;
  },
};

export const documentsApi = {
  uploadMaterial: async (curriculumVersionId: number, file: File, password?: string): Promise<Material> => {
    const formData = new FormData();
    formData.append('file', file);
    if (password) {
      formData.append('password', password);
    }
    const res = await apiClient.post(`/documents/${curriculumVersionId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  getMaterial: async (id: number): Promise<Material> => {
    const res = await apiClient.get(`/documents/${id}`);
    return res.data;
  },

  listMaterials: async (curriculumVersionId: number): Promise<Material[]> => {
    const res = await apiClient.get(`/documents/list/${curriculumVersionId}`);
    return res.data;
  },

  getSections: async (materialId: number): Promise<Section[]> => {
    const res = await apiClient.get(`/documents/${materialId}/sections`);
    return res.data;
  },

  deleteMaterial: async (id: number): Promise<void> => {
    await apiClient.delete(`/documents/${id}`);
  },
};

export const topicsApi = {
  extractTopics: async (curriculumVersionId: number, sectionIds: number[]): Promise<Topic[]> => {
    const res = await apiClient.post('/topics/extract', {
      curriculum_version_id: curriculumVersionId,
      section_ids: sectionIds,
    });
    return res.data.topics;
  },

  createTopic: async (name: string, curriculumVersionId: number, summary?: string, tags?: string[]): Promise<Topic> => {
    const res = await apiClient.post('/topics/create', {
      name,
      curriculum_version_id: curriculumVersionId,
      summary,
      tags,
    });
    return res.data;
  },

  listTopics: async (curriculumVersionId: number): Promise<Topic[]> => {
    const res = await apiClient.get(`/topics/list/${curriculumVersionId}`);
    return res.data;
  },

  getClusters: async (curriculumVersionId: number) => {
    const res = await apiClient.get(`/topics/clusters/${curriculumVersionId}`);
    return res.data;
  },
};

export const lessonsApi = {
  generateLesson: async (
    outlineId: number, 
    title: string, 
    numLessons: number = 1,
    durationMinutes: number = 45,
    targetAudience: string = 'general'
  ): Promise<Lesson> => {
    const res = await apiClient.post('/lessons/generate', {
      outline_id: outlineId,
      title,
      num_lessons: numLessons,
      duration_minutes: durationMinutes,
      target_audience: targetAudience,
    });
    return res.data;
  },

  createLesson: async (
    outlineId: number, 
    title: string, 
    objectives?: string[],
    timeline?: object[],
    topics?: string[]
  ): Promise<Lesson> => {
    const res = await apiClient.post('/lessons/create', {
      outline_id: outlineId,
      title,
      objectives,
      timeline,
      topics,
    });
    return res.data;
  },

  getLesson: async (id: number): Promise<Lesson> => {
    const res = await apiClient.get(`/lessons/${id}`);
    return res.data;
  },

  listLessons: async (outlineId: number): Promise<Lesson[]> => {
    const res = await apiClient.get(`/lessons/list/${outlineId}`);
    return res.data;
  },

  updateLesson: async (
    id: number,
    title?: string,
    objectives?: string[],
    timeline?: object[],
    topics?: string[]
  ): Promise<Lesson> => {
    const res = await apiClient.put(`/lessons/${id}`, {
      title,
      objectives,
      timeline,
      topics,
    });
    return res.data;
  },
};

export const slidesApi = {
  generateSlides: async (lessonId: number): Promise<Slides> => {
    const res = await apiClient.post(`/slides/generate/${lessonId}`);
    return res.data;
  },

  setYaml: async (lessonId: number, yamlContent: string): Promise<Slides> => {
    const res = await apiClient.put(`/slides/yaml/${lessonId}`, {
      yaml_content: yamlContent,
    });
    return res.data;
  },

  renderHtml: async (lessonId: number): Promise<Slides> => {
    const res = await apiClient.post(`/slides/render/${lessonId}`);
    return res.data;
  },

  getSlides: async (lessonId: number): Promise<Slides> => {
    const res = await apiClient.get(`/slides/${lessonId}`);
    return res.data;
  },
};
