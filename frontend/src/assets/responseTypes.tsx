export type childNodeResponse = {
  search_id: string;
  parent: string;
  children: childNode[];
  count_children: number;
};

export type childNode = {
  id: string;
  name: string;
  sequence_no: number;
  level: number;
};
