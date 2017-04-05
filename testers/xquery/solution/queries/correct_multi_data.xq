declare variable $dataset0 external;
declare variable $dataset1 external;

<output>
{
    let $in0 := $dataset0/input/in
    return <out>{string($in0[1])}</out>
}
{
    let $in1 := $dataset1/input/in
    return <out>{string($in1[2])}</out>
}
</output>
