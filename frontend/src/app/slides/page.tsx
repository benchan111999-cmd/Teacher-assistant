'use client';

import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Card, Button, Spinner } from '@/components/ui';
import { curriculumApi, lessonsApi, slidesApi } from '@/lib/api';
import { Lesson, Slides } from '@/types/api';

export default function SlidesPage() {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [selectedLesson, setSelectedLesson] = useState<number | null>(null);
  const [slides, setSlides] = useState<Slides | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadLessons();
  }, []);

  useEffect(() => {
    if (selectedLesson) {
      loadSlides(selectedLesson);
    } else {
      setSlides(null);
    }
  }, [selectedLesson]);

  const loadLessons = async () => {
    try {
      const versions = await curriculumApi.listVersions();
      const outlineGroups = await Promise.all(
        versions.map((version) => curriculumApi.listOutlines(version.id))
      );
      const lessonGroups = await Promise.all(
        outlineGroups.flat().map((outline) => lessonsApi.listLessons(outline.id))
      );
      const allLessons = lessonGroups.flat();
      setLessons(allLessons);
      if (allLessons.length > 0 && !selectedLesson) {
        setSelectedLesson(allLessons[0].id);
      }
    } catch (error) {
      console.error('Failed to load lessons:', error);
      setLessons([]);
    }
  };

  const loadSlides = async (lessonId: number) => {
    try {
      const data = await slidesApi.getSlides(lessonId);
      setSlides(data);
    } catch {
      setSlides(null);
    }
  };

  const handleGenerateSlides = async () => {
    if (!selectedLesson) return;
    
    setLoading(true);
    try {
      const data = await slidesApi.generateSlides(selectedLesson);
      setSlides(data);
    } catch (error: any) {
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRenderHtml = async () => {
    if (!selectedLesson) return;
    
    setLoading(true);
    try {
      const data = await slidesApi.renderHtml(selectedLesson);
      setSlides(data);
      
      if (data.html) {
        const newWindow = window.open('', '_blank');
        newWindow?.document.write(data.html);
      }
    } catch (error: any) {
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleYamlChange = async (yaml: string) => {
    if (!selectedLesson || !yaml) return;
    
    try {
      const data = await slidesApi.setYaml(selectedLesson, yaml);
      setSlides(data);
    } catch (error) {
      console.error('Failed to save YAML:', error);
    }
  };

  return (
    <Layout title="Slides">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-medium mb-4">Select Lesson</h3>
          
          {lessons.length === 0 ? (
            <p className="text-gray-500 mb-4">
              No lessons available. Create one in Lessons first.
            </p>
          ) : (
            <select
              value={selectedLesson?.toString() || ''}
              onChange={(e) => setSelectedLesson(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">Select a lesson</option>
              {lessons.map((lesson) => (
                <option key={lesson.id} value={lesson.id}>
                  {lesson.title}
                </option>
              ))}
            </select>
          )}
          
          <Button 
            onClick={handleGenerateSlides} 
            disabled={!selectedLesson}
            className="mt-4 w-full"
          >
            Generate Slides
          </Button>
          
          <Button 
            onClick={handleRenderHtml} 
            disabled={!selectedLesson || !slides?.yaml}
            variant="secondary"
            className="mt-2 w-full"
          >
            Preview HTML
          </Button>
        </Card>

        <Card className="p-6 col-span-2">
          <h3 className="text-lg font-medium mb-4">YAML Content</h3>
          
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : !slides ? (
            <p className="text-gray-500 text-center py-8">
              Select a lesson and generate slides to see YAML content.
            </p>
          ) : (
            <textarea
              value={slides.yaml || ''}
              onChange={(e) => handleYamlChange(e.target.value)}
              className="w-full h-96 px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm"
              placeholder="YAML content will appear here..."
            />
          )}
        </Card>

        <Card className="p-6 col-span-full">
          <h3 className="text-lg font-medium mb-4">HTML Preview</h3>
          
          {slides?.html ? (
            <div 
              className="prose max-w-none"
              dangerouslySetInnerHTML={{ __html: slides.html }}
            />
          ) : (
            <p className="text-gray-500 text-center py-8">
              Click "Preview HTML" to see the rendered slides.
            </p>
          )}
        </Card>
      </div>
    </Layout>
  );
}
