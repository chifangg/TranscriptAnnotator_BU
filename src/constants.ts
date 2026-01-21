export const server_address = "http://localhost:8000/api"

export interface Message {
    speaker: string;
    content: string;
    timestamp: string;
}

export interface Segment {
    title: string;
    messages: Message[];
}

export interface Transcript {
    filename: string;
    segments: Segment[];
}

export interface Annotation {
    id: number;
    messageIndices: number[];
    label: string;
    description: string;
    timestamp: string;
    x?: number;
    y?: number;
}


export type CategoryAssignment = {
    transcriptFile: string;
    annotationId: number;
  }
export type Category = {
    label: string; annotations: CategoryAssignment[];
}