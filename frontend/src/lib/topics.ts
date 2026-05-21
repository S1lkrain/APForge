import topicRegistry from "@data/topic_registry.json";

export type TopicOption = {
  value: string;
  label: string;
};

export const TOPIC_OPTIONS: TopicOption[] = topicRegistry.topics.map((topic) => ({
  value: topic.slug,
  label: topic.label,
}));
