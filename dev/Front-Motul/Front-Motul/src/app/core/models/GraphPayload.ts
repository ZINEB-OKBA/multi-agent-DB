import {GraphSeries} from "./GraphSeries";

export interface GraphPayload {
    type: 'bar' | 'line' | 'pie';
    title?: string;
    x?: string[];
    series: GraphSeries[];
    yLabel?: string;
    unit?: string;
}

