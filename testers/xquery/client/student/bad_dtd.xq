declare variable $dataset0 external;

<output>
{
    for $in in $dataset0/input/in
    return <in>{string($in)}</in>
}
</output>
