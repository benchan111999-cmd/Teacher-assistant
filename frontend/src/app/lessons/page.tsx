'use client';

import { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Card, Button, Badge, Spinner } from '@/components/ui';
import { curriculumApi, lessonsApi } from '@/lib/api';
import { Lesson, Outline } from '@/types/api';

export default function LessonsPage() {
  const [outlines, setOutlines] = useState<Outline[]>([]);
  const [selectedOutline, setSelectedOutline] = useState<number | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadOutlines();
  }, []);

  useEffect(() => {
    if (selectedOutline) {
      loadLessons(selectedOutline);
    }
  }, [selectedOutline]);

  const loadOutlines = async () => {
    try {
      const versions = await curriculumApi.listVersions();
      const outlineGroups = await Promise.all(
        versions.map((version) => curriculumApi.listOutlines(version.id))
      );
      const allOutlines = outlineGroups.flat();
      setOutlines(allOutlines);
      if (allOutlines.length > 0 && !selectedOutline) {
        setSelectedOutline(allOutlines[0].id);
      }
    } catch (error) {
      console.error('Failed to load outlines:', error);
      setOutlines([]);
    }
  };

  const loadLessons = async (outlineId: number) => {
    setLoading(true);
    try {
      const data = await lessonsApi.listLessons(outlineId);
      setLessons(data);
    } catch (error) {
      console.error('Failed to load lessons:', error);
      setLessons([]);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!selectedOutline) return;
    
    const title = prompt('Enter lesson title:');
    if (!title) return;
    
    setLoading(true);
    try {
      const lesson = await lessonsApi.generateLesson(selectedOutline, title);
      setLessons([...lessons, lesson]);
    } catch (error: any) {
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const parseJson = (jsonStr?: string): any => {
    if (!jsonStr) return null;
    try {
      return JSON.parse(jsonStr);
    } catch {
      return null;
    }
  };

  return (
    <Layout title="Lessons">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-medium mb-4">Select Outline</h3>
          
          {outlines.length === 0 ? (
            <p className="text-gray-500 mb-4">
              No outlines available. Create one in Curriculum first.
            </p>
          ) : (
            <select
              value={selectedOutline?.toString() || ''}
              onChange={(e) => setSelectedOutline(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              {outlines.map((o) => (
                <option key={o.id} value={o.id}>
                  Outline #{o.id}
                </option>
              ))}
            </select>
          )}
          
          <Button 
            onClick={handleGenerate} 
            disabled={!selectedOutline}
            className="mt-4 w-full"
          >
            + Generate Lesson Plan
          </Button>
        </Card>

        <Card className="p-6 col-span-2">
          <h3 className="text-lg font-medium mb-4">Lessons</h3>
          
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : lessons.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              No lessons yet. Generate one to get started.
            </p>
          ) : (
            <div className="space-y-4">
              {lessons.map((lesson) => {
                const objectives = parseJson(lesson.objectives);
                const timeline = parseJson(lesson.timeline);
                
                return (
                  <div
                    key={lesson.id}
                    className="p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-start justify-between">
                      <h4 className="font-medium">{lesson.title}</h4>
                      <span className="text-sm text-gray-500">
                        ID: {lesson.id}
                      </span>
                    </div>
                    
                    {objectives && objectives.length > 0 && (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-gray-600">Objectives:</p>
                        <ul className="mt-1 text-sm">
                          {objectives.map((obj: string, i: number) => (
                            <li key={i}>• {obj}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {timeline && timeline.length > 0 && (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-gray-600">Timeline:</p>
                        <div className="mt-1 space-y-1">
                          {timeline.map((item: any, i: number) => (
                            <div key={i} className="text-sm">
                              <span className="text-gray-500">{item.time}:</span> {item.activity}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
}
