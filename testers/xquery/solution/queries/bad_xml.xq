declare variable $dataset0 external;

<output>
{
    for $in in $dataset0/input/in
    return <out>{string($in)}</out>
}
</output>
