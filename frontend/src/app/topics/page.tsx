'use client';

import { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Card, Button, Badge, Spinner } from '@/components/ui';
import { curriculumApi, topicsApi } from '@/lib/api';
import { Version, Topic } from '@/types/api';

export default function TopicsPage() {
  const [versions, setVersions] = useState<Version[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [clusters, setClusters] = useState<Record<string, Topic[]>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadVersions();
  }, []);

  useEffect(() => {
    if (selectedVersion) {
      loadTopics(selectedVersion);
    }
  }, [selectedVersion]);

  const loadVersions = async () => {
    try {
      const data = await curriculumApi.listVersions();
      setVersions(data);
      if (data.length > 0) {
        setSelectedVersion(data[0].id);
      }
    } catch (error) {
      console.error('Failed to load versions:', error);
    }
  };

  const loadTopics = async (versionId: number) => {
    setLoading(true);
    try {
      const data = await topicsApi.listTopics(versionId);
      setTopics(data);
      
      const clusterData = await topicsApi.getClusters(versionId);
      setClusters(clusterData);
    } catch (error) {
      console.error('Failed to load topics:', error);
    } finally {
      setLoading(false);
    }
  };

  const parseTags = (tagsStr?: string): string[] => {
    if (!tagsStr) return [];
    try {
      return JSON.parse(tagsStr);
    } catch {
      return [];
    }
  };

  return (
    <Layout title="Topics">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-medium mb-4">Select Version</h3>
          
          <select
            value={selectedVersion?.toString() || ''}
            onChange={(e) => setSelectedVersion(parseInt(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          >
            {versions.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name} ({v.year})
              </option>
            ))}
          </select>
          
          <Button 
            onClick={() => selectedVersion && loadTopics(selectedVersion)}
            variant="secondary"
            className="mt-4 w-full"
          >
            Refresh Topics
          </Button>
        </Card>

        <Card className="p-6 col-span-2">
          <h3 className="text-lg font-medium mb-4">
            Topics ({topics.length})
          </h3>
          
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : topics.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              No topics yet. Upload materials and extract topics first.
            </p>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {topics.map((topic) => (
                <div
                  key={topic.id}
                  className="p-4 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium">{topic.name}</h4>
                      {topic.summary && (
                        <p className="text-sm text-gray-600 mt-1">{topic.summary}</p>
                      )}
                      {topic.tags && (
                        <div className="flex gap-1 mt-2">
                          {parseTags(topic.tags).map((tag) => (
                            <Badge key={tag} variant="info">{tag}</Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    {topic.cluster_id && (
                      <span className="text-xs text-gray-400">
                        Cluster: {topic.cluster_id}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="p-6 col-span-full">
          <h3 className="text-lg font-medium mb-4">Topic Clusters</h3>
          
          {Object.keys(clusters).length === 0 ? (
            <p className="text-gray-500">No clusters available.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(clusters).map(([clusterId, clusterTopics]) => (
                <div key={clusterId} className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium mb-2">
                    {clusterId === 'unclustered' ? 'Unclustered' : `Cluster ${clusterId}`}
                  </h4>
                  <p className="text-sm text-gray-500">{clusterTopics.length} topics</p>
                  <ul className="mt-2 text-sm">
                    {clusterTopics.slice(0, 5).map((t) => (
                      <li key={t.id} className="truncate">• {t.name}</li>
                    ))}
                    {clusterTopics.length > 5 && (
                      <li className="text-gray-400">+ {clusterTopics.length - 5} more</li>
                    )}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
}