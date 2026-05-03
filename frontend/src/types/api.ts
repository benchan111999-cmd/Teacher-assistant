export interface Version {
  id: number;
  name: string;
  year: number;
  notes?: string;
}

export interface Outline {
  id: number;
  curriculum_version_id: number;
  items: string;
}

export interface Material {
  id: number;
  curriculum_version_id: number;
  file_name: string;
  file_type: string;
  parsed_at?: string;
  status: string;
}

export interface Section {
  id: number;
  material_id: number;
  title: string;
  body: string;
  position: number;
}

export interface Topic {
  id: number;
  curriculum_version_id?: number;
  name: string;
  summary?: string;
  tags?: string;
  cluster_id?: string;
  subtopics?: Subtopic[];
}

export interface Subtopic {
  id: number;
  topic_id?: number;
  name: string;
  summary?: string;
  position?: number;
}

export interface Lesson {
  id: number;
  outline_id: number;
  title: string;
  objectives?: string;
  timeline?: string;
  topics?: string;
}

export interface Slides {
  id: number;
  lesson_id: number;
  yaml?: string;
  html?: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

export interface ListResponse<T> {
  items: T[];
}
